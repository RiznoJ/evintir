"""
=============================================================================
fetch_representatives.py — Tech Watch: transcribe representative videos
=============================================================================
WHAT THIS SCRIPT DOES: for clusters awaiting a blurb, runs
  sources/fetch_transcript.sh against ONLY the representative video (never
  every video in a cluster) and records the result in data/watchlist.json.

  sources/fetch_transcript.sh takes a single YouTube URL and decides its own
  output path/filename (sources/transcripts/<upload-date>_<title-slug>.md) —
  it does not accept an output path from the caller. This script learns the
  actual saved path by parsing the "Saved: <path>" line the shell script
  prints to stdout on success; it never precomputes a path.

  No captions -> that video is marked no_captions and the NEXT-priority
  video in the same cluster becomes the representative and gets ONE fallback
  attempt. If that also lacks captions, the cluster is left with an empty
  blurb for a human to write by hand — no further fallback attempts.

  Any other failure is recorded in that video's `error` field. One failure
  never aborts the batch.

WHO RUNS IT: you, manually, after approving/creating clusters in
  data/clusters_draft.json. Local only — never runs in CI (YouTube blocks
  datacenter IPs for extraction).
=============================================================================
"""

import argparse
import subprocess
import sys
import time

from techwatch_common import (
    REPO_ROOT,
    load_config,
    load_watchlist,
    save_watchlist,
    load_clusters_draft,
    save_clusters_draft,
)

FETCH_SCRIPT = REPO_ROOT / "sources" / "fetch_transcript.sh"
SLEEP_SECONDS = 2
SAVE_EVERY = 5


def eligible_clusters(clusters_data, watchlist):
    out = []
    for c in clusters_data["clusters"]:
        if c["status"] not in ("draft", "approved"):
            continue
        if c["blurb"]:
            continue
        rep = watchlist["videos"].get(c["representative_video_id"])
        if rep is None or rep.get("status") == "transcribed":
            continue
        out.append(c)
    return out


def pick_next_representative(cluster, failed_id, channel_priority):
    candidates = [v for v in cluster["videos"] if v["video_id"] != failed_id]
    if not candidates:
        return None

    def sort_key(v):
        return (channel_priority.get(v["channel"], 999), v["published"])

    return min(candidates, key=sort_key)["video_id"]


def run_fetch_transcript(video_url):
    """Returns (status, detail). status in {"success","no_captions","error"}.
    On success, detail is the saved transcript path parsed from stdout."""
    result = subprocess.run(
        [str(FETCH_SCRIPT), video_url],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode == 0:
        saved_path = None
        for line in result.stdout.splitlines():
            if line.startswith("Saved: "):
                saved_path = line[len("Saved: "):].strip()
        if saved_path:
            return "success", saved_path
        return "error", "fetch_transcript.sh exited 0 but printed no 'Saved:' line"

    stderr = result.stderr.strip()
    if "no English caption file produced" in stderr:
        return "no_captions", stderr[-500:]
    return "error", stderr[-500:]


def main():
    parser = argparse.ArgumentParser(description="Fetch transcripts for cluster representative videos.")
    parser.add_argument("--limit", type=int, default=10, help="Max clusters to process this run (default 10).")
    parser.add_argument("--cluster-id", help="Only process this cluster.")
    parser.add_argument("--dry-run", action="store_true", help="List what would be fetched, call nothing.")
    args = parser.parse_args()

    if not FETCH_SCRIPT.exists():
        print(f"ERROR: {FETCH_SCRIPT} not found", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    channel_priority = {c["display_name"]: c["representative_priority"] for c in config["channels"]}

    watchlist = load_watchlist()
    clusters_data = load_clusters_draft()

    candidates = eligible_clusters(clusters_data, watchlist)
    if args.cluster_id:
        candidates = [c for c in candidates if c["cluster_id"] == args.cluster_id]
        if not candidates:
            print(f"Cluster '{args.cluster_id}' is not eligible (not draft/approved, blurb already set, or representative already transcribed).")
            return

    candidates = candidates[: args.limit]

    print(f"{len(candidates)} cluster(s) eligible this run.")
    if args.dry_run:
        for c in candidates:
            rep = watchlist["videos"].get(c["representative_video_id"], {})
            print(f"  [{c['cluster_id']}] rep={c['representative_video_id']} \"{rep.get('title', '?')}\" ({rep.get('url', '?')})")
        print("\n--dry-run: no transcripts fetched, no files written.")
        return

    attempted = 0
    for c in candidates:
        rep_id = c["representative_video_id"]
        rep_entry = watchlist["videos"][rep_id]

        print(f"[{c['cluster_id']}] fetching representative {rep_id}: {rep_entry['title']}")
        status, detail = run_fetch_transcript(rep_entry["url"])
        attempted += 1

        if status == "success":
            rep_entry["status"] = "transcribed"
            rep_entry["transcript_path"] = detail
            rep_entry["error"] = None
            print(f"  transcribed -> {detail}")
        elif status == "no_captions":
            rep_entry["status"] = "no_captions"
            rep_entry["error"] = None
            print("  no captions available; trying next-priority video in cluster")
            fallback_id = pick_next_representative(c, rep_id, channel_priority)
            if fallback_id:
                c["representative_video_id"] = fallback_id
                fb_entry = watchlist["videos"][fallback_id]
                time.sleep(SLEEP_SECONDS)
                fb_status, fb_detail = run_fetch_transcript(fb_entry["url"])
                attempted += 1
                if fb_status == "success":
                    fb_entry["status"] = "transcribed"
                    fb_entry["transcript_path"] = fb_detail
                    fb_entry["error"] = None
                    print(f"  fallback {fallback_id} transcribed -> {fb_detail}")
                elif fb_status == "no_captions":
                    fb_entry["status"] = "no_captions"
                    fb_entry["error"] = None
                    print(f"  fallback {fallback_id} also has no captions; leaving blurb empty for hand-write")
                else:
                    fb_entry["error"] = fb_detail
                    print(f"  fallback {fallback_id} failed: {fb_detail}")
            else:
                print("  no other video in cluster to try; leaving blurb empty for hand-write")
        else:
            rep_entry["error"] = detail
            print(f"  ERROR: {detail}")

        if attempted % SAVE_EVERY == 0:
            save_watchlist(watchlist)
            save_clusters_draft(clusters_data)

        time.sleep(SLEEP_SECONDS)

    save_watchlist(watchlist)
    save_clusters_draft(clusters_data)
    print(f"\nDone. {attempted} fetch attempt(s) across {len(candidates)} cluster(s). Wrote data/watchlist.json and data/clusters_draft.json")


if __name__ == "__main__":
    main()
