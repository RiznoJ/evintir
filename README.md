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
    from that run's scores — it is not recorded as a 0. The sparkline plots
    absent runs as 0 for display continuity, but that's a rendering choice,
    not a claim that "0 risk" was measured.

Each pipeline run appends one `{generated_at, scores}` entry to
`data/risk_history.json` (capped at the most recent `MAX_HISTORY_RUNS`, ~50
days at 4 runs/day) — the history is accumulated across real runs, not
backfilled or interpolated.

Both scores share the same honesty caveat as the rest of this project: a
documented placeholder rubric, not a validated model.

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
