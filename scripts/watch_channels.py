"""
=============================================================================
watch_channels.py — Tech Watch: ongoing detection (runs in CI)
=============================================================================
WHAT THIS SCRIPT DOES: polls each configured channel's YouTube RSS feed
  (~15 most recent videos per channel — plenty for catching new uploads
  between backfills, not enough for a historical backfill; that's
  index_channels.py's job, run locally) and merges new videos into
  data/watchlist.json as status "indexed". Never overwrites an existing
  entry.

  STANDARD LIBRARY ONLY (urllib.request, xml.etree.ElementTree) — no pip
  install step needed in CI.

WHO RUNS IT: GitHub Actions on a schedule (.github/workflows/techwatch.yml),
  and you, manually, any time. Detection only — no yt-dlp, no transcripts,
  no API key here (YouTube blocks datacenter IPs for extraction, so that
  work stays local).
=============================================================================
"""

import argparse
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from techwatch_common import load_config, load_watchlist, save_watchlist, utcnow_iso

ATOM_NS = "http://www.w3.org/2005/Atom"
YT_NS = "http://www.youtube.com/xml/schemas/2015"
USER_AGENT = "Evintir-techwatch/1.0"
TIMEOUT_SECONDS = 20


def fetch_feed(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return resp.read()


def parse_feed(xml_bytes):
    root = ET.fromstring(xml_bytes)
    entries = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        video_id_el = entry.find(f"{{{YT_NS}}}videoId")
        title_el = entry.find(f"{{{ATOM_NS}}}title")
        published_el = entry.find(f"{{{ATOM_NS}}}published")
        link_el = entry.find(f"{{{ATOM_NS}}}link")

        video_id = video_id_el.text if video_id_el is not None else None
        if not video_id:
            continue

        href = link_el.get("href") if link_el is not None else None
        entries.append({
            "video_id": video_id,
            "title": title_el.text if title_el is not None else "",
            "published_raw": published_el.text if published_el is not None else None,
            "url": href or f"https://www.youtube.com/watch?v={video_id}",
        })
    return entries


def to_date_str(published_raw):
    if not published_raw:
        return None
    try:
        return datetime.fromisoformat(published_raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser(description="Poll channel RSS feeds for new Tech Watch videos.")
    parser.add_argument("--dry-run", action="store_true", help="Print counts, write nothing.")
    args = parser.parse_args()

    config = load_config()
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=config["rss_window_days"])).isoformat()
    effective_floor = max(config["floor_date"], cutoff)

    watchlist = load_watchlist()
    videos = watchlist["videos"]

    total_polled = 0
    total_added = 0

    for channel in config["channels"]:
        try:
            entries = parse_feed(fetch_feed(channel["channel_id"]))
        except (urllib.error.URLError, ET.ParseError, TimeoutError) as exc:
            print(f"[{channel['key']}] ERROR: {exc}", file=sys.stderr)
            continue

        total_polled += len(entries)
        added = 0
        for e in entries:
            if e["video_id"] in videos:
                continue
            published = to_date_str(e["published_raw"])
            if published is None or published < effective_floor:
                continue
            added += 1
            if args.dry_run:
                continue
            videos[e["video_id"]] = {
                "video_id": e["video_id"],
                "channel_key": channel["key"],
                "channel_display": channel["display_name"],
                "source_tier": channel["source_tier"],
                "title": e["title"],
                "url": e["url"],
                "published": published,
                "first_seen": utcnow_iso(),
                "topics": [],
                "relevant": None,
                "cluster_id": None,
                "status": "indexed",
                "transcript_path": None,
                "error": None,
            }
        total_added += added
        print(f"[{channel['key']}] polled={len(entries)} added={added}")

    status_counts = {}
    for v in videos.values():
        status_counts[v["status"]] = status_counts.get(v["status"], 0) + 1

    print(f"\ntotal polled: {total_polled}  total added: {total_added}")
    print(f"queue size by status: {status_counts}")

    if args.dry_run:
        print("\n--dry-run: no files written.")
    else:
        save_watchlist(watchlist)
        print("\nWrote data/watchlist.json")


if __name__ == "__main__":
    main()
