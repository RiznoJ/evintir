"""
=============================================================================
publish_techwatch.py — Tech Watch: the approve-before-publish gate
=============================================================================
WHAT THIS SCRIPT DOES: reads data/clusters_draft.json, takes ONLY clusters
  with status "approved" AND a non-empty headline and blurb, and writes the
  public data/techwatch.json. Approved clusters still missing a blurb are
  skipped and listed so you know what's pending.

  This is the only script that touches the file the (not-yet-built) Tech
  Watch tab will read. Nothing publishes without status: "approved" set by
  hand in data/clusters_draft.json first.

WHO RUNS IT: you, manually, as the last step of the pipeline.
=============================================================================
"""

import argparse

from techwatch_common import load_config, load_clusters_draft, save_json_techwatch

DISCLOSURE = (
    "Tech Watch entries are short summaries of publicly available video "
    "content, drafted from automatic captions and reviewed before "
    "publication. They describe what the linked source videos discuss; "
    "they are not verified factual claims and are not analytical "
    "assessments. See Analyst Notes for sourced, confidence-labeled analysis."
)


def build_item(cluster, channel_tier):
    videos = [
        {
            "title": v["title"],
            "channel": v["channel"],
            "source_tier": channel_tier.get(v["channel"], "secondary"),
            "published": v["published"],
            "url": v["url"],
        }
        for v in sorted(cluster["videos"], key=lambda v: v["published"])
    ]
    return {
        "id": cluster["cluster_id"],
        "headline": cluster["headline"],
        "blurb": cluster["blurb"],
        "topic": cluster["topic"],
        "theaters": cluster["theaters"],
        "date_start": cluster["date_start"],
        "date_end": cluster["date_end"],
        "videos": videos,
    }


def main():
    parser = argparse.ArgumentParser(description="Publish approved Tech Watch clusters to data/techwatch.json.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be published, write nothing.")
    args = parser.parse_args()

    config = load_config()
    channel_tier = {c["display_name"]: c["source_tier"] for c in config["channels"]}

    clusters_data = load_clusters_draft()
    approved = [c for c in clusters_data["clusters"] if c["status"] == "approved"]

    ready = [c for c in approved if c["headline"] and c["blurb"]]
    pending = [c for c in approved if not (c["headline"] and c["blurb"])]

    items = [build_item(c, channel_tier) for c in ready]
    items.sort(key=lambda item: item["date_end"], reverse=True)

    print(f"approved clusters: {len(approved)}")
    print(f"publishing: {len(items)}")
    if pending:
        print(f"skipped (approved but missing headline/blurb — still pending): {len(pending)}")
        for c in pending:
            print(f"  [{c['cluster_id']}] headline={c['headline']!r} blurb={c['blurb']!r}")

    if args.dry_run:
        print("\n--dry-run: no files written.")
        return

    out = {
        "generated_utc": "",
        "disclosure": DISCLOSURE,
        "items": items,
    }
    save_json_techwatch(out)
    print("\nWrote data/techwatch.json")


if __name__ == "__main__":
    main()
