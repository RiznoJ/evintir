"""
=============================================================================
index_channels.py — Tech Watch historical backfill: build the video index
=============================================================================
WHAT THIS SCRIPT DOES:
  For each configured YouTube channel (config/techwatch.json), lists every
  video via yt-dlp's flat-playlist mode (metadata only — no download, no
  transcript, no API key) and records the ones published on or after the
  Tech Watch floor date into data/watchlist.json.

  This is the one-time (or occasional re-run) historical backfill. Ongoing
  detection between backfills is watch_channels.py's job (RSS-based, runs
  in CI). This script exists because YouTube's RSS feed only returns the
  ~15 most recent videos per channel — nowhere near enough for a backfill
  to 28 Feb 2026.

WHO RUNS IT: you, manually. Never scheduled — it walks a channel's entire
  upload history and is not something CI should do on its own.

SAFETY:
  - Never overwrites an existing watchlist entry's status, transcript_path,
    cluster_id, or error. A video already indexed is left alone entirely.
  - --dry-run prints counts and writes nothing.
=============================================================================
"""

import argparse
import json
import subprocess
import sys
import time

from techwatch_common import (
    WATCHLIST_PATH,
    load_config,
    load_watchlist,
    save_watchlist,
    resolve_ytdlp,
    utcnow_iso,
    yyyymmdd_to_iso,
)


def list_channel_videos(ytdlp_path, channel_url):
    """Flat-playlist dump: fast, no per-video network hit. Yields dicts with
    at least id/title, upload_date often missing or null."""
    videos_url = channel_url.rstrip("/") + "/videos"
    result = subprocess.run(
        [
            ytdlp_path,
            "--flat-playlist",
            "--dump-json",
            "--skip-download",
            "--sleep-requests", "2",
            videos_url,
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"yt-dlp failed listing {videos_url}: {result.stderr.strip()[-500:]}"
        )
    entries = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        entries.append(json.loads(line))
    return entries


def fallback_upload_date(ytdlp_path, video_id):
    """One-shot metadata lookup for a single video when flat-playlist gave
    no upload_date. Never retried in a loop — either this resolves it or
    the video is stored as needs_date."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    result = subprocess.run(
        [
            ytdlp_path,
            "--dump-json",
            "--skip-download",
            "--sleep-requests", "2",
            video_url,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        meta = json.loads(result.stdout.splitlines()[0])
    except json.JSONDecodeError:
        return None
    return meta.get("upload_date")


def process_channel(ytdlp_path, channel, floor_date, watchlist, dry_run):
    stats = {
        "channel": channel["key"],
        "total_found": 0,
        "within_window": 0,
        "already_indexed": 0,
        "newly_added": 0,
        "needs_date": 0,
    }

    try:
        entries = list_channel_videos(ytdlp_path, channel["url"])
    except Exception as exc:
        print(f"  ERROR: {exc}", file=sys.stderr)
        stats["error"] = str(exc)
        return stats

    stats["total_found"] = len(entries)
    videos = watchlist["videos"]

    for entry in entries:
        video_id = entry.get("id")
        if not video_id:
            continue

        if video_id in videos:
            stats["already_indexed"] += 1
            continue

        title = entry.get("title", "") or ""
        upload_date_raw = entry.get("upload_date")

        if not upload_date_raw:
            upload_date_raw = fallback_upload_date(ytdlp_path, video_id)

        published = yyyymmdd_to_iso(upload_date_raw)

        if published is None:
            stats["needs_date"] += 1
            new_entry = {
                "video_id": video_id,
                "channel_key": channel["key"],
                "channel_display": channel["display_name"],
                "source_tier": channel["source_tier"],
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "published": None,
                "first_seen": utcnow_iso(),
                "topics": [],
                "relevant": None,
                "cluster_id": None,
                "status": "needs_date",
                "transcript_path": None,
                "error": None,
            }
            if not dry_run:
                videos[video_id] = new_entry
            stats["newly_added"] += 1
            continue

        if published < floor_date:
            continue

        stats["within_window"] += 1
        stats["newly_added"] += 1
        new_entry = {
            "video_id": video_id,
            "channel_key": channel["key"],
            "channel_display": channel["display_name"],
            "source_tier": channel["source_tier"],
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "published": published,
            "first_seen": utcnow_iso(),
            "topics": [],
            "relevant": None,
            "cluster_id": None,
            "status": "indexed",
            "transcript_path": None,
            "error": None,
        }
        if not dry_run:
            videos[video_id] = new_entry

    return stats


def main():
    parser = argparse.ArgumentParser(description="Backfill the Tech Watch video index.")
    parser.add_argument("--channel", help="Only index this channel key (e.g. sandboxx).")
    parser.add_argument("--dry-run", action="store_true", help="Print counts, write nothing.")
    args = parser.parse_args()

    config = load_config()
    floor_date = config["floor_date"]

    channels = config["channels"]
    if args.channel:
        channels = [c for c in channels if c["key"] == args.channel]
        if not channels:
            print(f"ERROR: unknown channel key '{args.channel}'", file=sys.stderr)
            sys.exit(1)

    try:
        ytdlp_path = resolve_ytdlp()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    watchlist = load_watchlist()

    print(f"floor_date: {floor_date}")
    all_stats = []
    for channel in channels:
        print(f"\n[{channel['key']}] {channel['display_name']}")
        stats = process_channel(ytdlp_path, channel, floor_date, watchlist, args.dry_run)
        all_stats.append(stats)
        if "error" in stats:
            continue
        print(f"  total found:      {stats['total_found']}")
        print(f"  within window:    {stats['within_window']}")
        print(f"  already indexed:  {stats['already_indexed']}")
        print(f"  newly added:      {stats['newly_added']}")
        print(f"  needs_date hits:  {stats['needs_date']}")

    if args.dry_run:
        print("\n--dry-run: no files written.")
    else:
        save_watchlist(watchlist)
        print(f"\nWrote {WATCHLIST_PATH.relative_to(WATCHLIST_PATH.parent.parent)}")


if __name__ == "__main__":
    main()
