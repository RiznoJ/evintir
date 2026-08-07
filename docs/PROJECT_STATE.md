# Evintir — Project State

Maintained per CLAUDE.md operating notes. Overwrite stale entries, don't append forever.

## Works now that didn't before
- **Per-country News tab filtering**: `fetch_feeds.py` tags each ingested event with
  `country_tags: []` (COUNTRY_KEYWORDS, word-boundary keyword match on headline).
  The country popup filters on `country_tags.includes(name)` instead of the old
  coarse `region === matchRegion` match, which collapsed most countries into
  "Global" and showed unrelated world news. Zero-match shows an explicit
  "No country-specific coverage in the current window." message.
- **XSS hardening**: all feed-derived text run through a shared `esc()` before
  any `innerHTML` insertion; `source_url` validated http(s)-only via `safeUrl()`
  before use in an `<a href>`.
- **Source freshness indicator**: `fetch_feeds.py` writes a `sources[]` array
  (per-feed `last_success`, carried forward across a failing run so an outage
  doesn't erase the last real success). Fixed a real gap while building this —
  feedparser doesn't raise on a dead URL, it returns `bozo=1` with no entries,
  so the old try/except never caught it; now that's treated as failure too.
  UI renders a color-coded "updated Xh ago" strip.
- **Risk trend sparkline**: `data/risk_history.json` gets one appended
  `{generated_at, scores}` entry per pipeline run (capped at 200). Formula —
  `sum(event.risk_score * CATEGORY_SEVERITY[category] * recency_weight)` per
  country, capped at 10 — documented in README.md "Risk scoring methodology".
  Inline SVG sparkline renders in each country's map popup.
- **Country-compare view**: two dropdowns + trend direction (RISING/FALLING/
  STEADY/INSUFFICIENT HISTORY from risk_history) + shared flagged categories
  intersection — deliberately not a plain side-by-side snapshot.
- **Printable Analyst Brief**: `@media print` collapses the page to just the
  brief, single column; nav/map/filters/table hidden; UNCLASSIFIED banner and
  the brief's own source/confidence notes stay visible. "Print / Save as PDF"
  button, no new dependency.
- **Shareable deep link**: `?country=<name>&tab=<news|analyst|analysis>` pans
  the map and opens that country's popup. `country` is checked against
  `COUNTRIES` with an exact `hasOwnProperty` match before touching the DOM —
  verified this rejects wrong-case input, HTML injection, and
  `__proto__`/`constructor` prototype-pollution attempts.
- **NOTICE.md**: catalogues the 22 Wikimedia emblem files (6 license-spot-
  checked live this session — found the UK file is CC BY-SA/GFDL, not PD like
  the rest, and flagged as an open action item) and the 5 RSS feed sources.
- **Reference shipping corridors overlay**: `data/shipping_lanes.geojson`
  (1.17MB, 3 features: Major/Middle/Minor, CC BY 4.0, CIA 2012 source via
  newzealandpaul/Shipping-Lanes). Toggleable Leaflet layer, off by default,
  labeled everywhere as static 2012 reference data — not live AIS.
- **Two new Analyst Notes posts**: North Korea (p12, "North Korea's Compute
  Problem: Missiles Are the Visible Layer") and Japan (p13, "Japan Is
  Rebuilding the Machinery of Strategic Autonomy"), both tagged DEEP
  ANALYSIS, Medium confidence, 12 and 10 sources respectively — all URLs
  verified to match the supplied list exactly (scripted diff-check, no
  transcription errors). Both countries already had emblem/badge data and
  NOTICE.md license entries from earlier today; `activeCountries()` now
  includes both, confirmed via a Node simulation against the real file.
  Zero current events.json coverage for either country (no NK/Japan-specific
  feed in `FEEDS` yet) — their map badges will show the honest "no event
  data" grey ring and empty News tab until that's added, not a bug.
  Content was reformatted into the real schema (reporting/analysis/
  confidence/openQuestion/sources) without rewriting any sentence — the
  "Sourced Reporting" and "Open Questions" sections became single flowing
  paragraphs (`reporting`/`openQuestion` fields don't paragraph-split in the
  current render), while "Assessment" mapped to `analysis`, which does.

## Files changed this session
`scripts/fetch_feeds.py`, `index.html`, `README.md`, `NOTICE.md` (new),
`docs/PROJECT_STATE.md` (new), `data/events.json`, `data/risk_history.json`
(new), `data/shipping_lanes.geojson` (new), `data/notes.json` (+p12, +p13).

## Known limitations / unfinished pieces
- Country/region keyword classification is still headline-only word-boundary
  matching — documented crudeness, not solved.
- **Maritime EEZ overlay: investigated, not built.** Marine Regions' public
  WFS (`geo.vliz.be`, layer `MarineRegions:eez`) works, but even scoped to
  just the 22 tracked countries + 7 chokepoint territories, full-resolution
  polygons for 6 of the larger ones alone (Russia/US/Australia/Indonesia/UK/
  China) totaled ~44MB with 25+ second individual requests — confirms the
  original plan's "100+ MB" concern rather than resolving it. Needs geometry
  simplification (mapshaper or a Python GIS lib) before it's viable, which is
  a real new-dependency decision, not something to slip in passing. See
  NOTICE.md "Investigated, not integrated" for the exact numbers.
- No headless-browser tool was available this session, so every UI change
  was verified via `node --check` on the extracted inline script, JSON
  parsing, and Node simulations of the actual render logic against real
  regenerated data — NOT an actual browser render. A manual
  `python3 -m http.server` + click-through pass (map popups, sparkline,
  compare dropdowns, print preview, deep link, lane toggle) is still worth
  doing before calling this fully verified in-browser.
- UK coat-of-arms emblem (`countries.js`) is CC BY-SA/GFDL and needs a proper
  attribution line somewhere on-page; currently just an `<img>` with `alt`.
- All work this session is committed locally on `main`, NOT pushed — user
  wanted to review before anything goes to the live GitHub Pages site.

## Next logical step
Manual browser click-through pass (see above), then push if it looks right.
After that: the 9 planned Analyst Notes posts (NK/SK/Japan, 3 each) are a
separate writing session per the project's own workflow (drafting happens
elsewhere, Claude Code is for mechanical execution only). EEZ overlay is a
dedicated future session once geometry-simplification tooling is decided on.
