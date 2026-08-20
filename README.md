# Evintir — Public-Source Strategic Monitor

> **Unclassified // Public sources only.** A personal learning and portfolio
> project. Not affiliated with any government organization.

This project is a public, unclassified strategic monitoring dashboard built as
a personal learning and portfolio project. The goal is to practice coding,
GitHub workflows, public data integration, OSINT methodology, event
classification, and analyst-style briefing. The dashboard focuses on the
Middle East, U.S. defense posture, Russia/Ukraine, the Indo-Pacific, cyber
incidents, maritime chokepoints, and energy risk. No proprietary consulting
work, client data, classified information, private credentials, or restricted
sources are included.

<!-- TODO(you): add a screenshot here once the site is live.
     ![Dashboard screenshot](docs/screenshot.png) -->

## How it works

```
public RSS feeds ──> scripts/fetch_feeds.py ──> data/events.json ──> index.html
                     (GitHub Actions runs         (the "database")     (map, cards,
                      this every 6 hours)                              feed, brief)
```

- **`index.html`** — the entire dashboard: a Leaflet world map, regional risk
  cards, filterable event feed, and a self-generating analyst brief.
- **`data/events.json`** — every event, in a fixed schema. The schema is the
  contract between the data pipeline and the display.
- **`scripts/fetch_feeds.py`** — pulls public RSS feeds, classifies events by
  region/category with keyword rules, assigns a placeholder risk score, and
  writes the JSON.
- **`.github/workflows/update-feeds.yml`** — schedules the script every 6
  hours via GitHub Actions and commits the refreshed data.

## Event schema

`id · date · region · location · lat/lon · category · event_type ·
source_name · source_url · summary · why_it_matters · confidence ·
risk_score · tags · country_tags`

`data/events.json` also carries a top-level `sources[]` array (one entry per
RSS feed, with a `last_success` timestamp — drives the "Source Freshness"
indicator) alongside `events[]`. `data/risk_history.json` is a separate,
append-only file: one `{generated_at, scores}` entry per pipeline run,
capped at the most recent 200 runs — see "Risk scoring methodology" below.

## Run it locally

```bash
python -m http.server        # from the project folder
# open http://localhost:8000
```

To refresh data manually: `pip install -r requirements.txt` then
`python scripts/fetch_feeds.py`.

## Risk scoring methodology

Two distinct scores exist, and they answer different questions:

- **`risk_score`** (0-9, on each individual event) — a placeholder keyword
  rubric (see `RISK_KEYWORDS` in `fetch_feeds.py`): base 3, bumped by
  severity keywords found in the headline. This is a single event's score.
- **Per-country trend score** (0-10, shown as the sparkline on each country's
  map popup) — computed fresh every pipeline run from that run's tagged
  events, in `compute_country_scores()`:

  ```
  score = sum( event.risk_score * CATEGORY_SEVERITY[event.category] * recency_weight )
          over every event tagged with that country this run, capped at 10
  ```

  - `CATEGORY_SEVERITY` weights category by how directly it implies
    escalation risk (Military 1.0, Cyber 0.8, Maritime 0.7, Energy 0.6,
    Economic/Information 0.5, Geopolitical 0.4 default) — a Military-tagged
    headline contributes more than a general Geopolitical one at the same
    `risk_score`.
  - `recency_weight` decays linearly from 1.0 (published now) to 0.0 across
    the 7-day retention window (`MAX_AGE_DAYS`), so the score reflects recent
    weighted activity, not a raw event count or a single stale headline.
  - A country with zero tagged events in a given run is simply **absent**
    from that run's scores — it is not recorded as a 0. Absence can mean
    "genuinely no elevated activity that run," but it can also mean "no
    feed coverage of this country that run" or "this country wasn't being
    tracked yet when this history entry was recorded" — those cases are
    indistinguishable in the data, so nothing displayed here claims to
    know which one happened.
  - **Missing-observation rule (applies everywhere risk history is
    displayed):** an absent score is treated as a gap, never as a measured
    0. Both the country popup's sparkline and Country Compare's trend
    direction filter out history entries with no score for that country
    before computing anything — they do not plot or average in a 0. A
    country with fewer than 2 real (non-absent) data points shows an
    explicit "insufficient history" / "no scored risk-history data" state
    instead of a misleading flat line or invented trend.

Each pipeline run appends one `{generated_at, scores}` entry to
`data/risk_history.json` (capped at the most recent `MAX_HISTORY_RUNS`, ~50
days at 4 runs/day) — the history is accumulated across real runs, not
backfilled or interpolated.

Both scores share the same honesty caveat as the rest of this project: a
documented placeholder rubric, not a validated model.

## China Strategic Reference Layer

An opt-in, geographic reference layer of publicly-sourced Chinese military
and strategic sites, reachable from China's country popup on the Situation
Map ("Explore Strategic Map"). It is **static context, not real-time force
disposition** — every entry is a fixed public-source description with a
citation, `verification_status`, and `last_reviewed` date, and it never
factors into `risk_score`, country risk trends, or any other event math on
this site.

Sites are shown in two tiers — **Major Sites** (the default view) and **All
Curated Sites**, which additionally includes lower-confidence or
theater-level entries — filterable by category (Navy, Air, Ground, Rocket,
Joint/Command, Information/Intelligence, Central/Political-Military) and
searchable by name, branch, category, or location. Data lives in
`data/reference/china.geojson` and is fetched only when the layer is
opened, not on page load.

Research inspiration and attribution: Joseph Wen's public PLA-sites map
(credited by name in the layer's own panel and in
[NOTICE.md](NOTICE.md)) — Evintir's layer is an independently curated,
much smaller subset written in Evintir's own words, not a copy of his
selection or descriptions, and his map is never embedded or depended on at
runtime.

## Tech Watch

A filterable index of defense-technology developments drawn from three
YouTube channels (Sandboxx and Cappy Army, secondary sources; DARPAtv, a
primary source), covering 28 February 2026 forward. **Tech Watch is a
collection layer, not analysis** — every entry describes what its linked
source videos discuss ("Covers reported...", "Discusses..."), never an
assertion about the world, and is visibly and structurally separate from
the hand-written, confidence-labeled Analyst Notes.

The unit of the feed is a development, not a video: multiple channels
covering the same thing collapse into one entry with a headline, a short
blurb drafted from an auto-caption transcript, and links to every source
video underneath, each labeled by channel and source tier (primary/
secondary). Nothing publishes without a human explicitly approving it in
`data/clusters_draft.json` first.

Filter by topic, theater, channel, or date range, or search headlines and
blurbs directly on the [Tech Watch tab](techwatch.html). Detection (which
videos exist) runs on a schedule in GitHub Actions; extraction (captions,
via `yt-dlp`) runs locally, since YouTube blocks datacenter IPs — see
[docs/TECHWATCH.md](docs/TECHWATCH.md) for the full pipeline, the closed
topic/theater vocabularies, and the run order.

## Honest limitations

- Keyword classification is crude and mislabels some items; machine-ingested
  events are marked **Unverified** until human review.
- Risk scores use a simple placeholder rubric, not a validated model.
- Map markers are region centroids, not precise event locations.
- Public sources only; no claim of completeness or real-time accuracy.

## Safety & ethics

Public, unclassified information only. No leaked, hacked, or restricted
material. No API keys or secrets in the repository (`.env` is gitignored; see
`.env.example`). Analysis is labeled with confidence levels and limitations;
the tone aims to be analytical and balanced, not partisan.

See [NOTICE.md](NOTICE.md) for the full external data/asset source and
license catalogue (country emblem files, RSS feed providers).

## Credits & inspiration

Inspired by public open-source world-monitor dashboards, especially
[worldmonitor](https://github.com/koala73/worldmonitor). This project shares
no code with it and was built independently from scratch; it is a simplified,
educational take on the same idea. Map tiles by [CARTO](https://carto.com/)
with data © OpenStreetMap contributors. Mapping by
[Leaflet](https://leafletjs.com/).

## What I learned

<!-- TODO(you): write this section YOURSELF, in your own words, after the
     teardown sessions. Interviewers can tell the difference. Cover: what a
     repo/commit is, how the pipeline works, what the schema does, what you'd
     improve next. -->

## Roadmap

- [ ] Human review workflow for unverified events
- [ ] Documented risk-scoring rubric (replace keyword placeholder)
- [ ] Per-region "what changed today" deltas
- [ ] AI-assisted summarization with source citations
- [ ] Learning log (docs/learning-log.md)
