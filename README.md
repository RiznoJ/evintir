# WATCHSTANDER — Public-Source Strategic Monitor

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
risk_score · tags`

## Run it locally

```bash
python -m http.server        # from the project folder
# open http://localhost:8000
```

To refresh data manually: `pip install -r requirements.txt` then
`python scripts/fetch_feeds.py`.

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
