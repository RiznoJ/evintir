"""
=============================================================================
fetch_feeds.py — the data pipeline for WATCHSTANDER
=============================================================================
WHAT THIS SCRIPT DOES (read this first):
  1. Downloads several public RSS feeds (RSS = a standard "here are my
     latest articles" format that most news sites publish for free).
  2. Turns each article into an "event" matching the project schema.
  3. Classifies each event by REGION and CATEGORY using keyword rules.
  4. Assigns a placeholder RISK SCORE using a simple keyword rubric.
  5. Writes everything to data/events.json — which the dashboard reads.

WHO RUNS IT:
  - You, manually:            python scripts/fetch_feeds.py
  - GitHub Actions, on a schedule (see .github/workflows/update-feeds.yml)

HONESTY NOTES (say these in interviews — they make you MORE credible):
  - Keyword classification is crude. It mislabels things. That's why every
    auto-ingested event gets confidence "Unverified" until a human reviews it.
  - The risk rubric is a placeholder, not a validated model.
  - Map coordinates are REGION CENTROIDS (a dot near the middle of the
    region), not precise event locations. RSS headlines don't carry lat/lon.
=============================================================================
"""

import json
import hashlib
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser  # the one external library: pip install feedparser

# ---------------------------------------------------------------------------
# 1. FEEDS — public, free, no API keys. Each feed gets a DEFAULT region and
#    category; keyword rules below can override them per-article.
#    NOTE: feed URLs change over time. If one stops working, the script
#    skips it and keeps going (see the try/except in fetch_all).
# ---------------------------------------------------------------------------
FEEDS = [
    {"url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
     "source": "CISA Advisories", "region": "Cyber", "category": "Cyber"},
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml",
     "source": "BBC World", "region": "Global", "category": "Geopolitical"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml",
     "source": "Al Jazeera", "region": "Global", "category": "Geopolitical"},
    {"url": "https://gcaptain.com/feed/",
     "source": "gCaptain (maritime)", "region": "Global", "category": "Maritime"},
    {"url": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=20",
     "source": "U.S. DoD Releases", "region": "United States", "category": "Military"},
]

# ---------------------------------------------------------------------------
# 2. CLASSIFICATION RULES — if a headline contains any keyword on the left,
#    the event is routed to the region/category on the right. First match
#    wins, top to bottom, so put more specific rules higher.
# ---------------------------------------------------------------------------
REGION_RULES = [
    (["israel", "gaza", "hezbollah", "lebanon", "iran", "houthi", "red sea",
      "yemen", "syria", "iraq", "hormuz", "saudi"], "Middle East"),
    (["ukraine", "russia", "kyiv", "moscow", "black sea", "crimea", "nato"],
     "Europe / Russia-Ukraine"),
    (["taiwan", "china", "south china sea", "pla ", "beijing", "philippines",
      "indo-pacific", "korea"], "Indo-Pacific"),
    (["pentagon", "u.s. navy", "us navy", "indopacom", "centcom", "carrier"],
     "United States"),
    (["ransomware", "cyberattack", "cyber attack", "malware", "phishing",
      "vulnerability", "cve-"], "Cyber"),
]

CATEGORY_RULES = [
    (["ransomware", "cyber", "malware", "hack", "breach", "vulnerability",
      "phishing", "cve-"], "Cyber"),
    (["tanker", "shipping", "vessel", "port", "strait", "canal", "maritime",
      "naval", "navy", "fleet"], "Maritime"),
    (["oil", "gas", "pipeline", "lng", "energy", "grid", "power plant",
      "refinery"], "Energy"),
    (["missile", "drone", "strike", "airstrike", "troops", "exercise",
      "military", "deployment", "artillery"], "Military"),
    (["sanction", "export control", "tariff", "semiconductor", "economy"],
     "Economic"),
    (["disinformation", "influence operation", "propaganda"], "Information"),
]

# Placeholder risk rubric: base 3, bumped by severity keywords, capped at 9.
# This is deliberately simple and documented as a limitation.
RISK_KEYWORDS = {
    "attack": 3, "strike": 3, "missile": 3, "explosion": 3, "killed": 3,
    "drone": 2, "ransomware": 2, "breach": 2, "seized": 2, "clash": 2,
    "warning": 1, "advisory": 1, "exercise": 1, "sanctions": 1, "tension": 1,
}

# Map dots: approximate centroid per region (LIMITATION: not event-precise).
REGION_COORDS = {
    "Middle East": (29.0, 45.0),
    "Europe / Russia-Ukraine": (49.0, 32.0),
    "Indo-Pacific": (18.0, 118.0),
    "United States": (38.0, -97.0),
    "Cyber": (20.0, -30.0),      # symbolic mid-Atlantic dot for global cyber
    "Global": (10.0, 0.0),
}

MAX_AGE_DAYS = 7      # keep the dashboard focused on the last week
MAX_EVENTS = 120      # cap file size


def classify(text, rules, default):
    """Return the first rule label whose keywords appear in the text.

    BUG FIX (found by testing): plain substring matching classified
    'Ukraine REPORTS missile attack' as Maritime because 'port' appears
    inside 'reports'. We now match whole words/phrases only, using \b
    (a regex "word boundary"). Lesson: always test classifiers with
    realistic inputs — the failure modes are never the ones you expect.
    """
    t = text.lower()
    for keywords, label in rules:
        if any(re.search(r"\b" + re.escape(k.strip()) + r"\b", t) for k in keywords):
            return label
    return default


def score_risk(text):
    """Placeholder rubric: 3 + keyword bumps, capped 1-9."""
    t = text.lower()
    score = 3 + sum(v for k, v in RISK_KEYWORDS.items() if k in t)
    return max(1, min(score, 9))


def entry_to_event(entry, feed_cfg):
    """Convert one RSS entry into one schema-shaped event dict."""
    title = re.sub(r"\s+", " ", entry.get("title", "")).strip()
    if not title:
        return None

    # Stable id: hash of the link (or title), so re-runs don't duplicate.
    key = entry.get("link", title)
    eid = "RSS-" + hashlib.sha1(key.encode()).hexdigest()[:10]

    # Published date -> YYYY-MM-DD (fall back to today if the feed omits it).
    if entry.get("published_parsed"):
        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    if datetime.now(timezone.utc) - dt > timedelta(days=MAX_AGE_DAYS):
        return None  # too old — skip

    region = classify(title, REGION_RULES, feed_cfg["region"])
    category = classify(title, CATEGORY_RULES, feed_cfg["category"])
    lat, lon = REGION_COORDS.get(region, REGION_COORDS["Global"])

    return {
        "id": eid,
        "date": dt.strftime("%Y-%m-%d"),
        "region": region,
        "location": region,          # headline-level data has no finer location
        "lat": lat, "lon": lon,
        "category": category,
        "event_type": "Public news report",
        "source_name": feed_cfg["source"],
        "source_url": entry.get("link", ""),
        "summary": title,
        "why_it_matters": "Auto-ingested from public RSS; pending analyst annotation.",
        "confidence": "Unverified",  # honest default for machine-ingested items
        "risk_score": score_risk(title),
        "tags": ["rss", "auto-ingested"],
    }


def fetch_all():
    events, seen = [], set()
    for feed_cfg in FEEDS:
        try:
            parsed = feedparser.parse(feed_cfg["url"])
            for entry in parsed.entries[:25]:
                ev = entry_to_event(entry, feed_cfg)
                if ev and ev["id"] not in seen:
                    seen.add(ev["id"])
                    events.append(ev)
            print(f"OK   {feed_cfg['source']}: {len(parsed.entries)} entries")
        except Exception as exc:  # one broken feed must not kill the run
            print(f"SKIP {feed_cfg['source']}: {exc}")
    events.sort(key=lambda e: (e["date"], e["risk_score"]), reverse=True)
    return events[:MAX_EVENTS]


def main():
    events = fetch_all()
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "Auto-generated from public RSS feeds. Confidence 'Unverified' "
                "means no human review yet. Coordinates are region centroids.",
        "events": events,
    }
    path = Path(__file__).resolve().parent.parent / "data" / "events.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {len(events)} events -> {path}")


if __name__ == "__main__":
    main()
