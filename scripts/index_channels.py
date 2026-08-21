"""
=============================================================================
index_channels.py — Tech Watch historical backfill: build the video index
=============================================================================
WHAT THIS SCRIPT DOES:
  For each configured YouTube channel (config/techwatch.json), lists its
  most recent videos via yt-dlp's flat-playlist mode (metadata only — no
  download, no transcript, no API key) and records the ones published on
  or after the Tech Watch floor date into data/watchlist.json.

  This is the one-time (or occasional re-run) historical backfill. Ongoing
  detection between backfills is watch_channels.py's job (RSS-based, runs
  in CI). This script exists because YouTube's RSS feed only returns the
  ~15 most recent videos per channel — nowhere near enough for a backfill
  to 28 Feb 2026.

  STOP CONDITION, NOT POST-FILTER: a channel's /videos listing comes back
  newest-first, so position in that list is a reliable proxy for recency.
  Earlier revisions of this script fetched the WHOLE upload history (no
  --playlist-end cap) and filtered by floor_date only after fetching each
  video's date — meaning it walked all the way back through a channel's
  entire history, firing an expensive one-by-one --dump-json fallback call
  for every old video with a missing flat-playlist date, only to then
  throw the result away for being too old. That cost 3h45m against three
  channels and wrote nothing to disk. Fixed by bounding the listing itself
  (--playlist-end) and by stopping the walk outright once several
  consecutive videos are confirmed older than the floor — never filtering
  after the fact.

WHO RUNS IT: you, manually. Never scheduled — it walks recent channel
  history and is not something CI should do on its own.

SAFETY:
  - Never overwrites an existing watchlist entry's status, transcript_path,
    cluster_id, or error. A video already indexed is left alone entirely.
  - --dry-run prints counts and writes nothing.
  - Checkpoints data/watchlist.json every CHECKPOINT_EVERY videos, not just
    at the end, so a kill/crash mid-run doesn't lose already-processed work.
=============================================================================
"""

import argparse
import json
import subprocess
import sys

from techwatch_common import (
    WATCHLIST_PATH,
    load_config,
    load_watchlist,
    save_watchlist,
    resolve_ytdlp,
    utcnow_iso,
    yyyymmdd_to_iso,
)

# Feb 28 2026 -> today is under 6 months; none of these channels post more
# than 150 videos in that span. This caps the worst case for the listing
# call itself, independent of the early-stop logic below.
PLAYLIST_END = 150

# After this many consecutive videos (walked newest-first) are confirmed
# older than floor_date, the rest of the channel's history is assumed to be
# entirely pre-floor too, and the walk stops rather than continuing to
# fetch/filter videos that will only ever be discarded.
CONSECUTIVE_PRE_FLOOR_STOP = 5

CHECKPOINT_EVERY = 20


def list_channel_videos(ytdlp_path, channel_url):
    """Flat-playlist dump, newest videos first, capped at PLAYLIST_END —
    fast, no per-video network hit. upload_date is often missing/null."""
    videos_url = channel_url.rstrip("/") + "/videos"
    result = subprocess.run(
        [
            ytdlp_path,
            "--flat-playlist",
            "--dump-json",
            "--skip-download",
            "--playlist-end", str(PLAYLIST_END),
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
    the video is stored as needs_date. Only ever called for videos still
    within the early-stop window (see process_channel) — never for videos
    the walk has already given up on.

    --extractor-args "youtube:player_client=android": the "web" client
    fails full single-video extraction with "The page needs to be
    reloaded." (confirmed by hand against a live video ID) — the exact
    issue sources/fetch_transcript.sh already documented and works around
    the same way. Without this, essentially every fallback call failed
    silently and returned None, which is why the first fixed run still
    landed ~94% of new videos in needs_date."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    result = subprocess.run(
        [
            ytdlp_path,
            "--dump-json",
            "--skip-download",
            "--extractor-args", "youtube:player_client=android",
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


def short_title(title, max_len=60):
    title = title or ""
    return title[:max_len] + ("…" if len(title) > max_len else "")


def new_watchlist_entry(channel, video_id, title, published, status):
    return {
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
        "status": status,
        "transcript_path": None,
        "error": None,
    }


def process_channel(ytdlp_path, channel, floor_date, watchlist, dry_run, on_video_processed):
    stats = {
        "channel": channel["key"],
        "total_found": 0,
        "within_window": 0,
        "already_indexed": 0,
        "newly_added": 0,
        "needs_date": 0,
        "stopped_early_at": None,
    }

    try:
        entries = list_channel_videos(ytdlp_path, channel["url"])
    except Exception as exc:
        print(f"  ERROR: {exc}", file=sys.stderr, flush=True)
        stats["error"] = str(exc)
        return stats

    stats["total_found"] = len(entries)
    videos = watchlist["videos"]
    consecutive_pre_floor = 0

    for i, entry in enumerate(entries, start=1):
        video_id = entry.get("id")
        if not video_id:
            continue

        if video_id in videos:
            stats["already_indexed"] += 1
            on_video_processed(dry_run)
            existing_published = videos[video_id].get("published")
            if existing_published and existing_published < floor_date:
                consecutive_pre_floor += 1
                if consecutive_pre_floor >= CONSECUTIVE_PRE_FLOOR_STOP:
                    stats["stopped_early_at"] = i
                    print(f"  [{channel['key']}] hit {CONSECUTIVE_PRE_FLOOR_STOP} consecutive "
                          f"pre-floor videos, stopping at {i}", flush=True)
                    break
            elif existing_published:
                consecutive_pre_floor = 0
            continue

        title = entry.get("title", "") or ""
        upload_date_raw = entry.get("upload_date")

        if not upload_date_raw:
            upload_date_raw = fallback_upload_date(ytdlp_path, video_id)

        published = yyyymmdd_to_iso(upload_date_raw)

        if published is None:
            stats["needs_date"] += 1
            if not dry_run:
                videos[video_id] = new_watchlist_entry(channel, video_id, title, None, "needs_date")
            stats["newly_added"] += 1
            print(f"  [{channel['key']}] {i}/{stats['total_found']} — unknown-date — {short_title(title)}", flush=True)
            on_video_processed(dry_run)
            continue

        print(f"  [{channel['key']}] {i}/{stats['total_found']} — {published} — {short_title(title)}", flush=True)

        if published < floor_date:
            consecutive_pre_floor += 1
            on_video_processed(dry_run)
            if consecutive_pre_floor >= CONSECUTIVE_PRE_FLOOR_STOP:
                stats["stopped_early_at"] = i
                print(f"  [{channel['key']}] hit {CONSECUTIVE_PRE_FLOOR_STOP} consecutive "
                      f"pre-floor videos, stopping at {i}", flush=True)
                break
            continue

        consecutive_pre_floor = 0
        stats["within_window"] += 1
        stats["newly_added"] += 1
        if not dry_run:
            videos[video_id] = new_watchlist_entry(channel, video_id, title, published, "indexed")
        on_video_processed(dry_run)

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
            print(f"ERROR: unknown channel key '{args.channel}'", file=sys.stderr, flush=True)
            sys.exit(1)

    try:
        ytdlp_path = resolve_ytdlp()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)

    watchlist = load_watchlist()

    processed_counter = {"n": 0}

    def on_video_processed(dry_run):
        processed_counter["n"] += 1
        if not dry_run and processed_counter["n"] % CHECKPOINT_EVERY == 0:
            save_watchlist(watchlist)
            print(f"  (checkpoint: saved data/watchlist.json after {processed_counter['n']} videos processed)", flush=True)

    print(f"floor_date: {floor_date}", flush=True)
    for channel in channels:
        print(f"\n[{channel['key']}] {channel['display_name']} — starting, up to {PLAYLIST_END} most recent videos", flush=True)
        stats = process_channel(ytdlp_path, channel, floor_date, watchlist, args.dry_run, on_video_processed)
        if "error" in stats:
            continue
        print(f"  total found:      {stats['total_found']}")
        print(f"  within window:    {stats['within_window']}")
        print(f"  already indexed:  {stats['already_indexed']}")
        print(f"  newly added:      {stats['newly_added']}")
        print(f"  needs_date hits:  {stats['needs_date']}")
        print(f"  stopped early at: {stats['stopped_early_at'] if stats['stopped_early_at'] else 'no (walked full capped list)'}", flush=True)

    if args.dry_run:
        print("\n--dry-run: no files written.", flush=True)
    else:
        save_watchlist(watchlist)
        print(f"\nWrote {WATCHLIST_PATH.relative_to(WATCHLIST_PATH.parent.parent)}", flush=True)


if __name__ == "__main__":
    main()
