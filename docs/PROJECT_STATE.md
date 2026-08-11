# Evintir — Project State

Maintained per CLAUDE.md operating notes. Overwrite stale entries, don't append forever.

## Works now that didn't before
- **China Strategic Reference Layer — Phase 2** (extends Phase 1, doesn't
  replace it): the strategic panel opened from China's country popup now has
  a Major/All tier toggle, 7 category-filter checkboxes, a live context
  summary, a text search, per-feature "View area on Wen's map" links, mapped
  verification labels, and a theater-level disclaimer — on top of everything
  Phase 1 already did (lazy load, own markerClusterGroup, own hexagon
  markers, Exit).
  - **Dataset expanded** from 14 to 31 features (`data/reference/china.geojson`
    fully replaced with the new set — theater commands, all 6 fleet HQs
    including a new North Sea Fleet, Dalian shipyard, 7 Rocket Force bases
    by number, 5 space/satellite sites, ASF/CSF/ISF, and 4
    cyber/technical-reconnaissance entries). Every feature now carries
    `importance` (major/secondary) and `verification_status`
    (verified/source-reported).
  - **Major/All tier toggle**: radio buttons, defaults to Major (28 of 31
    features); All shows all 31.
  - **7 category filter checkboxes** (Navy, Air, Ground, Rocket,
    Joint/Command, Information/Intelligence, Central/Political-Military),
    all on by default, combine with the tier toggle. Ground and
    Political-Military have styling/checkboxes ready but 0 matching entries
    in the current dataset — by design, not a bug (see "Known limitations").
  - **Context summary** at the top of the panel: curated-site count + a
    per-category breakdown (both recompute live off the actual filtered set,
    never hard-coded), plus China's CURRENT risk/events/analyst-note counts
    — computed once by `index.html` from the existing `DATA`/`NOTES`
    globals (via `window.activateChinaStrategic()`, mirroring the
    `window.cpTab` convention) and handed to the module as a read-only
    display value. `strategic-china.js` never reads `DATA`/`NOTES`/
    `COUNTRIES` itself.
  - **Search**: matches name/branch/category/location substrings against
    the currently-visible (tier+filter-respecting) set, shows up to 8
    results, selecting one uses `markerClusterGroup.zoomToShowLayer()` to
    un-cluster and focus that exact feature and open its popup. Empty
    query hides results; no-match shows an escaped "No matches for ..."
    note.
  - **Popup additions**: verification_status mapped to "Verified" /
    "Source-reported (single public source)"; a `/theater[- ]level/i` regex
    on `short_description` triggers an explicit "approximate theater-level
    area, not a precise facility" note; a "View area on Wen's map ↗" link
    built from that feature's own coordinates (never a specific pin of
    his), validated with the same `safeUrl()` helper as `source_url`.
  - **Panel footer**: small Wen attribution + "thousands more sites" credit
    line, linking to his base map (new tab, `noopener noreferrer`).
  - `china.geojson` load failure still fully non-fatal (re-tested by
    renaming the file again this session) — panel shows the unavailable
    note with no filter/search UI, Exit still works, rest of Evintir
    unaffected.

## Files changed this session
- **Rewrote**: `data/reference/china.geojson` (14 → 31 features, new schema
  fields `importance`/richer `verification_status` usage — same 12-key
  schema as Phase 1, nothing invented beyond what was provided).
- **Rewrote**: `js/strategic-china.js` (Phase 1's fetch/cache/marker/control
  scaffolding kept; added tier+category filter state, live summary/search
  rendering, Wen link + verification-label + theater-level popup additions).
- **Modified**: `index.html` — replaced the Phase 1 legend CSS with the
  Phase 2 panel CSS (summary/toggle/filters/search/credit + a sticky Exit
  button, see below), added `window.activateChinaStrategic()` next to
  `window.cpTab`, changed the popup button's `onclick` to call it.
- **Modified**: `NOTICE.md` (new "China Strategic Reference Layer" section:
  Joseph Wen attribution with title/date-accessed/non-mirror statement, plus
  the institutional source list), `README.md` (new "China Strategic
  Reference Layer" section: what it is, Major/All tiers, Wen attribution,
  explicit "static context, not real-time force disposition" framing
  matching the rest of the doc's honesty conventions).
- `docs/PROJECT_STATE.md` (this file).

## Verification performed (real, not assumed)
- `node --check` on both JS files (extracted index.html's inline script
  separately) — pass. `china.geojson` parses and every feature's property
  keys match the fixed schema — checked programmatically: 31 features, all
  unique ids, categories `{central-command:1, joint-command:2, navy:6,
  air:2, rocket:8, information-intelligence:12}`, importance `{major:28,
  secondary:3}`, verification `{verified:26, source-reported:5}`.
  Regex-scanned every `short_description` for "Strategic Support Force" —
  the two hits are both explicitly historical/lineage framing ("former...
  passed through the... to today's..."), not a reintroduction of SSF as a
  current entity.
- Reused the Chromium install from the Phase 1 session and ran real browser
  automation against `python3 -m http.server`:
  - global map unchanged (0 strategic markers, existing markers/badges
    still render); China popup → Explore Strategic Map still opens the view
  - Major default correctly shows 28; switching to All shows 31; summary
    breakdown line matches the programmatic category counts above exactly
  - unchecking the Rocket filter drops the total by exactly 8 (23) and
    zeroes just the Rocket count in the breakdown — filters and tier
    combine correctly
  - all 7 category checkboxes present
  - search for "Rocket Force Headquarters" returns it, selecting it opens
    its popup (title confirmed); a nonsense query shows an escaped
    "No matches for ..." note
  - switched to All, searched a theater-level entry (`csf-trb-east`),
    selected it: popup HTML captured and checked field-by-field — the
    theater-level disclaimer, "Source-reported (single public source)"
    verification label, and a correctly-coordinate-built Wen link
    (`&ll=32.06,118.797&z=11`) were all present
  - panel footer credit HTML confirmed present and correctly linked
  - **Bug found and fixed during testing**: exiting shortly after a search
    selection (which pans/zooms via `zoomToShowLayer`) left the map
    stranded at the search location instead of resetting to the global
    view — a Leaflet animation race between the in-flight zoom and the
    exit's own `setMaxZoom`/`setView`. Fixed in `deactivate()` by calling
    `map.stop()` first and reordering `setView` (non-animated) before
    `setMaxZoom`. Reproduced before the fix (raw center/zoom logged), then
    confirmed fixed (`[25,30]`, zoom 2, exactly) both with and without a
    prior search selection.
  - renamed `china.geojson` again: unavailable note shown, no filter/search
    UI leaks through while data is missing, Exit still works, rest of the
    page (cards, feed) unaffected. Restored the file, reconfirmed it parses.
  - `pageerror` listener stayed empty across every run — zero JS runtime
    errors.
  - **Second bug found and fixed on mobile (390×844)**: Phase 2's panel
    content is much taller than Phase 1's; the Exit button scrolled out of
    the panel's capped-height view along with everything else, with no
    visible affordance suggesting a user should scroll a small floating
    panel to find it. Fixed by making `.strategic-exit-btn`
    `position: sticky; bottom: -1px` within the panel's own scroll
    container — confirmed via bounding-box coordinates that Exit now stays
    inside the panel's visible box regardless of scroll position, and via a
    real (non-forced) click that it's genuinely reachable.

## Known limitations / unfinished pieces
- **31 features delivered, not the 32 described**: the task described "28
  core + a separate CWO/info-warfare block = 32," but only one JSON block
  was actually provided, and it already contained all the CWO-labeled
  entries (`cn-csf-3pla-legacy`, `cn-csf-cyber-ops-base`,
  `cn-csf-trb-east`, `cn-csf-trb-south`) — 31 total, no duplicates. Used
  exactly what was given rather than inventing a 32nd entry; see NEEDS MY
  REVIEW in the chat response.
- **Category-filter grouping**: the spec listed 7 checkbox labels against 8
  category values, with the last label ("Central/Political-Military")
  covering two category values. Implemented as one combined checkbox/count
  for `central-command` + `political-military` — consistent with the
  spec's own context-summary line, which likewise shows one combined
  "Central XX" rather than two separate counts. Flagged in case a literal
  8th checkbox is preferred instead.
- `ground` and `political-military` have full marker styling and their own
  filter checkboxes, but 0 entries in the current dataset use them — the
  checkboxes currently filter nothing, exactly as the brief said was fine.
- Search is a simple substring match over name/branch/category/location
  text, capped at 8 results — intentionally not a real search engine, per
  scope.
- All work this session is uncommitted, matching this project's "commit
  locally, review, then push" pattern.

## Next logical step
User review of the diff (`index.html`, `NOTICE.md`, `README.md`) plus the
two rewritten files (`data/reference/china.geojson`,
`js/strategic-china.js`) — see the chat response's "NEEDS MY REVIEW" list
(feature count discrepancy, category-checkbox grouping). Local preview:
`cd ~/Desktop/evintir && python3 -m http.server`, open
`http://localhost:8000`, click China's badge → "Explore Strategic Map" →
try the Major/All toggle, a category checkbox, and the search box. Commit
only on explicit request.
