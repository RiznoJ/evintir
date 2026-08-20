"""
=============================================================================
build_clusters.py — Tech Watch clustering: collapse videos into developments
=============================================================================
WHAT THIS SCRIPT DOES (pure Python, ZERO API calls, zero network calls):
  1. Relevance filter: classify each not-yet-processed video in
     data/watchlist.json as relevant/irrelevant against config/techwatch.json's
     closed topic keyword lists (DARPAtv videos are always relevant).
  2. Cluster relevant videos into "developments" — one entry per topic per
     rolling cluster_window_days window — so ~170 videos collapse into a
     few dozen clusters.
  3. Pick a representative video per cluster (by channel priority, then
     earliest publish date) and suggest a mechanical placeholder headline.
  4. Write data/clusters_draft.json.

FROZEN CLUSTERS: any cluster with status "approved" or "rejected" is never
  regenerated, never gains/loses members, never has its headline or blurb
  touched. Videos already assigned to ANY cluster (frozen or draft) are
  excluded from clustering again. New videos may form new clusters or join
  an existing DRAFT cluster (same topic, published inside that cluster's
  window) — draft clusters can keep growing across repeated runs until a
  human approves or rejects them.

WHO RUNS IT: you, manually, after index_channels.py / watch_channels.py
  add new rows to data/watchlist.json. Safe to re-run at any time.
=============================================================================
"""

import argparse
import re
from collections import defaultdict
from datetime import datetime, timedelta

from techwatch_common import load_config, load_watchlist, save_watchlist, load_clusters_draft, save_clusters_draft

CLICKBAIT_PATTERNS = [
    r"you won'?t believe",
    r"shocking",
    r"!!+",
    r"\bmust see\b",
]


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def add_days_iso(date_str, days):
    return (parse_date(date_str) + timedelta(days=days)).isoformat()


def is_allcaps_word(word):
    letters = [c for c in word if c.isalpha()]
    return len(letters) >= 2 and word == word.upper()


def suggest_headline(title, max_len=90):
    t = title
    for pat in CLICKBAIT_PATTERNS:
        t = re.sub(pat, "", t, flags=re.IGNORECASE)
    words = t.split()
    while words and is_allcaps_word(words[0]):
        words.pop(0)
    while words and is_allcaps_word(words[-1]):
        words.pop()
    t = " ".join(words).strip(" -:|")
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        t = title.strip()
    if len(t) > max_len:
        t = t[:max_len].rsplit(" ", 1)[0].rstrip(" -:|")
    return t


def video_record(video_id, entry):
    return {
        "video_id": video_id,
        "title": entry.get("title", ""),
        "channel": entry.get("channel_display", ""),
        "published": entry.get("published"),
        "url": entry.get("url", ""),
    }


def classify_relevance(entry, config):
    title_lower = (entry.get("title") or "").lower()
    if any(kw in title_lower for kw in config["exclude_keywords"]):
        return False, []

    matched = {}
    for topic, keywords in config["topics"].items():
        count = sum(1 for kw in keywords if kw in title_lower)
        if count:
            matched[topic] = count

    if not matched:
        if entry.get("channel_key") == "darpatv":
            return True, ["Doctrine, Budget & Policy"]
        return False, []

    return True, sorted(matched, key=lambda t: (-matched[t], t))


def unique_cluster_id(base_id, existing_ids):
    if base_id not in existing_ids:
        return base_id
    suffix_ord = ord("b")
    while f"{base_id}-{chr(suffix_ord)}" in existing_ids:
        suffix_ord += 1
    return f"{base_id}-{chr(suffix_ord)}"


def main():
    parser = argparse.ArgumentParser(description="Cluster Tech Watch videos into developments.")
    parser.add_argument("--dry-run", action="store_true", help="Print summary, write nothing.")
    parser.add_argument("--min-videos", type=int, default=1,
                         help="Suppress newly formed clusters with fewer than N videos (default 1 = no suppression).")
    args = parser.parse_args()

    config = load_config()
    cluster_window = config["cluster_window_days"]
    channel_priority = {c["display_name"]: c["representative_priority"] for c in config["channels"]}

    watchlist = load_watchlist()
    draft_data = load_clusters_draft()
    all_clusters = draft_data.get("clusters", [])

    frozen_clusters = [c for c in all_clusters if c["status"] in ("approved", "rejected")]
    draft_clusters = [c for c in all_clusters if c["status"] == "draft"]

    assigned_ids = set()
    for c in all_clusters:
        for v in c["videos"]:
            assigned_ids.add(v["video_id"])
    existing_cluster_ids = {c["cluster_id"] for c in all_clusters}

    relevant_count = 0
    irrelevant_count = 0
    by_topic = defaultdict(list)

    for video_id, entry in watchlist["videos"].items():
        if video_id in assigned_ids or entry.get("status") != "indexed":
            continue
        relevant, topics = classify_relevance(entry, config)
        entry["relevant"] = relevant
        if not relevant:
            entry["status"] = "irrelevant"
            irrelevant_count += 1
            continue
        entry["topics"] = topics
        relevant_count += 1
        primary_topic = topics[0]
        by_topic[primary_topic].append((video_id, entry))

    videos_joined_existing = 0
    new_clusters_created = 0

    for topic, vids in by_topic.items():
        vids.sort(key=lambda ve: ve[1]["published"])
        topic_draft_clusters = [c for c in draft_clusters if c["topic"] == topic]

        remaining = []
        for video_id, entry in vids:
            pub = entry["published"]
            joined = False
            for c in topic_draft_clusters:
                window_end = add_days_iso(c["date_start"], cluster_window)
                if c["date_start"] <= pub < window_end:
                    c["videos"].append(video_record(video_id, entry))
                    entry["status"] = "clustered"
                    entry["cluster_id"] = c["cluster_id"]
                    videos_joined_existing += 1
                    joined = True
                    break
            if not joined:
                remaining.append((video_id, entry))

        remaining.sort(key=lambda ve: ve[1]["published"])
        i = 0
        while i < len(remaining):
            anchor_id, anchor_entry = remaining[i]
            window_start = anchor_entry["published"]
            window_end = add_days_iso(window_start, cluster_window)
            bucket = [(anchor_id, anchor_entry)]
            j = i + 1
            while j < len(remaining) and remaining[j][1]["published"] < window_end:
                bucket.append(remaining[j])
                j += 1
            i = j

            if len(bucket) < args.min_videos:
                # Leave these videos unassigned (still "indexed") for a
                # future run to pick up once more accumulate.
                continue

            base_id = f"{slugify(topic)}-{window_start}"
            cluster_id = unique_cluster_id(base_id, existing_cluster_ids)
            existing_cluster_ids.add(cluster_id)

            new_cluster = {
                "cluster_id": cluster_id,
                "status": "draft",
                "topic": topic,
                "theaters": [],
                "suggested_headline": "",
                "headline": "",
                "blurb": "",
                "date_start": window_start,
                "date_end": bucket[-1][1]["published"],
                "representative_video_id": None,
                "videos": [video_record(vid, e) for vid, e in bucket],
                "human_edited": False,
                "error": None,
            }
            for vid, e in bucket:
                e["status"] = "clustered"
                e["cluster_id"] = cluster_id
            draft_clusters.append(new_cluster)
            topic_draft_clusters.append(new_cluster)
            new_clusters_created += 1

    for c in draft_clusters:
        c["videos"].sort(key=lambda v: v["published"])
        c["date_start"] = c["videos"][0]["published"]
        c["date_end"] = c["videos"][-1]["published"]

        def sort_key(v):
            return (channel_priority.get(v["channel"], 999), v["published"])

        rep = min(c["videos"], key=sort_key)
        c["representative_video_id"] = rep["video_id"]
        c["suggested_headline"] = suggest_headline(rep["title"])

    dist = defaultdict(int)
    for c in draft_clusters + frozen_clusters:
        dist[len(c["videos"])] += 1

    print(f"relevant: {relevant_count}  irrelevant: {irrelevant_count}")
    print(f"new clusters created: {new_clusters_created}  videos joined existing draft clusters: {videos_joined_existing}")
    print(f"clusters frozen (approved/rejected, untouched): {len(frozen_clusters)}")
    print(f"total draft clusters: {len(draft_clusters)}")
    print("videos-per-cluster distribution (count -> number of clusters):")
    for size in sorted(dist):
        print(f"  {size}: {dist[size]}")

    if args.dry_run:
        print("\n--dry-run: no files written.")
        return

    draft_data["clusters"] = frozen_clusters + draft_clusters
    save_clusters_draft(draft_data)
    save_watchlist(watchlist)
    print("\nWrote data/clusters_draft.json and data/watchlist.json")


if __name__ == "__main__":
    main()
