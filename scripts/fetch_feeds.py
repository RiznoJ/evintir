"""
=============================================================================
fetch_feeds.py — the data pipeline for WATCHSTANDER
=============================================================================
WHAT THIS SCRIPT DOES (read this first):
  1. Downloads several public RSS feeds (RSS = a standard "here are my
     latest articles" format that most news sites publish for free).
  2. Turns each article into an "event" matching the project schema.
  3. Classifies each event by REGION and CATEGORY using keyword rules, and
     tags it with zero or more COUNTRY_TAGS (see COUNTRY_KEYWORDS below) so
     the dashboard's per-country News tab can filter on country instead of
     the much coarser region.
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

# ---------------------------------------------------------------------------
# 2b. COUNTRY TAGS — separate from REGION_RULES above. Region is one coarse
#     bucket per event (used for map centroids); country_tags is a list of
#     ZERO OR MORE country names an event mentions, matched against countries.js
#     COUNTRIES keys (names here MUST match those keys exactly, including
#     "South Korea" not "Korea, South"). A single event can tag multiple
#     countries (e.g. an Israel-Iran story tags both). This is what the
#     dashboard's per-country News tab filters on instead of region, since
#     region alone collapses most countries into "Global".
#     Same limitation as REGION_RULES: crude keyword matching on the headline
#     only, no NLP/NER. Some countries (e.g. UAE, Kuwait) are common enough
#     to already be reasonably unambiguous by name; short country names alone
#     ("India", "Japan") can occasionally over-match in unrelated headlines
#     ("China" is safe, "Japan" occasionally isn't) — documented limitation,
#     not treated as a solved problem.
# ---------------------------------------------------------------------------
COUNTRY_KEYWORDS = {
    "United States":  ["united states", "pentagon", "white house", "washington"],
    "Russia":         ["russia", "russian", "moscow", "kremlin", "putin"],
    "Ukraine":        ["ukraine", "ukrainian", "kyiv", "kiev", "zelensky"],
    "China":          ["china", "chinese", "beijing", "xi jinping"],
    "India":          ["india", "indian", "new delhi", "modi"],
    "United Kingdom": ["united kingdom", "britain", "british", "london"],
    "France":         ["france", "french", "paris"],
    "Germany":        ["germany", "german", "berlin"],
    "Israel":         ["israel", "israeli", "tel aviv", "jerusalem", "netanyahu", "idf"],
    "Iran":           ["iran", "iranian", "tehran", "irgc"],
    "Pakistan":       ["pakistan", "pakistani", "islamabad"],
    "Japan":          ["japan", "japanese", "tokyo"],
    "South Korea":    ["south korea", "seoul"],
    "North Korea":    ["north korea", "pyongyang", "kim jong"],
    "Indonesia":      ["indonesia", "indonesian", "jakarta"],
    "Australia":      ["australia", "australian", "canberra"],
    "Mexico":         ["mexico", "mexican", "mexico city"],
    "Turkey":         ["turkey", "turkish", "ankara", "istanbul"],
    "Saudi Arabia":   ["saudi arabia", "saudi", "riyadh"],
    "United Arab Emirates": ["united arab emirates", "abu dhabi", "dubai", "emirati"],
    "Qatar":          ["qatar", "qatari", "doha"],
    "Kuwait":         ["kuwait", "kuwaiti"],
}

# ---------------------------------------------------------------------------
# 2c. PER-COUNTRY RISK HISTORY — documented, defensible formula, not a
#     validated model (same honesty standard as RISK_KEYWORDS above).
#     For each country with >=1 tagged event this run:
#       score = sum over its tagged events of
#               event.risk_score * CATEGORY_SEVERITY[event.category] * recency_weight
#     recency_weight decays LINEARLY to 0 across the MAX_AGE_DAYS window
#     (1.0 for an event published right now, 0.0 for one about to age out),
#     so a country's score reflects recent, weighted activity — not a raw
#     event count and not a single snapshot risk_score. Capped at 10 so it
#     stays on the same 0-10 scale as risk_score for the sparkline's y-axis.
#     This exact formula is also stated in README.md under "Risk scoring
#     methodology" — if you change it here, update that section too.
# ---------------------------------------------------------------------------
CATEGORY_SEVERITY = {
    "Military": 1.0, "Cyber": 0.8, "Maritime": 0.7, "Energy": 0.6,
    "Economic": 0.5, "Information": 0.5, "Geopolitical": 0.4,
}
MAX_HISTORY_RUNS = 200   # ~50 days of history at 4 runs/day; caps file size


def compute_country_scores(events):
    """country name -> weighted recent-risk score (see CATEGORY_SEVERITY above)."""
    now = datetime.now(timezone.utc)
    totals = {}
    for e in events:
        if not e.get("country_tags"):
            continue
        age_days = (now - datetime.strptime(e["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)).days
        recency_weight = max(0.0, 1 - age_days / MAX_AGE_DAYS)
        weight = e["risk_score"] * CATEGORY_SEVERITY.get(e["category"], 0.4) * recency_weight
        for country in e["country_tags"]:
            totals[country] = totals.get(country, 0.0) + weight
    return {country: round(min(score, 10), 1) for country, score in totals.items()}

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


def classify_countries(text):
    """Return every country name (COUNTRY_KEYWORDS key) mentioned in text.

    Unlike classify(), this doesn't stop at the first match — an event can
    legitimately tag more than one country (e.g. "Israel strikes target
    inside Iran"). Word-boundary matching, same as classify().
    """
    t = text.lower()
    return [name for name, keywords in COUNTRY_KEYWORDS.items()
            if any(re.search(r"\b" + re.escape(k.strip()) + r"\b", t) for k in keywords)]


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
        "country_tags": classify_countries(title),
    }


def fetch_all(prev_sources):
    """Fetch every feed, returning (events, source_status).

    source_status is one entry per FEEDS config, carrying a last_success
    timestamp forward from prev_sources (the previous run's output) when a
    feed fails this run — otherwise a feed going briefly offline would make
    the UI say "no data," when what's actually true is "this feed hasn't
    successfully pulled since <the last time it worked>." A feed that has
    never once succeeded gets last_success: null.
    """
    events, seen, source_status = [], set(), []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for feed_cfg in FEEDS:
        prev = prev_sources.get(feed_cfg["source"], {})
        try:
            parsed = feedparser.parse(feed_cfg["url"])
            # feedparser does NOT raise for a dead/unreachable URL — it just
            # returns an empty result with bozo=1 (malformed/unfetchable) and
            # no entries. Treat that the same as an exception: a well-formed
            # feed with zero entries (bozo=0) is the only case we still call
            # a success with nothing new to add.
            if parsed.get("bozo") and not parsed.entries:
                raise parsed.get("bozo_exception") or Exception("empty/unreachable feed")
            n = 0
            for entry in parsed.entries[:25]:
                ev = entry_to_event(entry, feed_cfg)
                if ev and ev["id"] not in seen:
                    seen.add(ev["id"])
                    events.append(ev)
                    n += 1
            print(f"OK   {feed_cfg['source']}: {len(parsed.entries)} entries")
            source_status.append({
                "source": feed_cfg["source"], "ok": True,
                "entries_this_run": n, "last_success": now,
            })
        except Exception as exc:  # one broken feed must not kill the run
            print(f"SKIP {feed_cfg['source']}: {exc}")
            source_status.append({
                "source": feed_cfg["source"], "ok": False,
                "entries_this_run": 0, "last_success": prev.get("last_success"),
            })
    events.sort(key=lambda e: (e["date"], e["risk_score"]), reverse=True)
    return events[:MAX_EVENTS], source_status


def main():
    path = Path(__file__).resolve().parent.parent / "data" / "events.json"
    prev_sources = {}
    if path.exists():
        try:
            prev = json.loads(path.read_text(encoding="utf-8"))
            prev_sources = {s["source"]: s for s in prev.get("sources", [])}
        except Exception:
            pass  # no usable previous run — every source just starts fresh

    events, source_status = fetch_all(prev_sources)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {
        "generated_at": generated_at,
        "note": "Auto-generated from public RSS feeds. Confidence 'Unverified' "
                "means no human review yet. Coordinates are region centroids.",
        "sources": source_status,
        "events": events,
    }
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {len(events)} events -> {path}")

    # Per-country risk history — APPENDED, not overwritten, so the dashboard
    # can draw a trend sparkline instead of only ever showing one snapshot.
    # See CATEGORY_SEVERITY / compute_country_scores above for the formula.
    history_path = path.parent / "risk_history.json"
    history = []
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8")).get("history", [])
        except Exception:
            history = []
    history.append({"generated_at": generated_at, "scores": compute_country_scores(events)})
    history = history[-MAX_HISTORY_RUNS:]
    history_out = {
        "note": "Per-country weighted-risk score, one entry per pipeline run. "
                "Formula: sum(event.risk_score * CATEGORY_SEVERITY[category] * "
                "recency_weight) over that country's tagged events this run, "
                "capped at 10. See README.md 'Risk scoring methodology'. "
                "Countries with zero tagged events in a given run are simply "
                "absent from that entry's scores, not scored as zero.",
        "history": history,
    }
    history_path.write_text(json.dumps(history_out, indent=2), encoding="utf-8")
    print(f"Appended risk-history entry ({len(history)} runs retained) -> {history_path}")


if __name__ == "__main__":
    main()
