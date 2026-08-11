# Evintir — Project State

Maintained per CLAUDE.md operating notes. Overwrite stale entries, don't append forever.

## Works now that didn't before
- **Per-article Print / Save as PDF (analyst.html)**: every post has its own
  "Print / Save as PDF" button. Clicking it stamps that one `.post` with
  `.print-target` and `<body>` with `.printing-single`, then calls
  `window.print()` — no PDF library. `@media print` rules keyed off those two
  classes hide nav, country filter strip, sort controls, other posts, footer
  credits, and the controls themselves; only the target article prints,
  along with both UNCLASSIFIED banners and the Evintir wordmark. Source
  links get their href expanded inline via `::after { content: attr(href) }`
  so URLs are readable on paper, not just clickable. Classes are cleared on
  `afterprint`. Verified with a real Playwright-generated PDF (3 pages for a
  long-form DEEP ANALYSIS post — confirms multi-page articles aren't cut
  off) and 42 automated browser assertions covering exactly what's
  visible/hidden in print media.
- **Copy Link (analyst.html)**: per-post "Copy Link" button next to Print,
  copies `location.origin + pathname + #post-<id>` via the Clipboard API
  (falls back to a hidden-textarea `execCommand('copy')` when
  `navigator.clipboard`/secure context isn't available). Shows a "Copied"
  label for ~1.6s. Doesn't change the existing `analyst.html#post-<id>` hash
  scheme or `scrollToHash()` — verified the copied URL, opened fresh in a
  new page, scrolls the right article into view.
- **Risk-history missing-value consistency fixed**: the country popup
  sparkline used to coerce a country's absent score in a given
  `risk_history.json` run to `0` (`(h.scores && h.scores[name]) || 0`),
  while Country Compare's `trendDirection()` already filtered absent scores
  out (`.filter(v => v != null)`) — same underlying data, two different
  interpretations of "no entry for this country this run." Confirmed via
  `compute_country_scores()` in `fetch_feeds.py`: a country only gets a
  scores entry when it had >=1 tagged event that run; absence is a genuine
  gap (could mean no elevated activity, no feed coverage, or the country
  wasn't tracked yet when that entry was recorded), not a measured 0. Fixed
  the popup to filter absent values the same way Compare does — both now
  agree: missing = gap, never a 0. Popup shows an explicit "No scored
  risk-history data for X yet" message when a country has zero real data
  points (previously silently plotted a flat zero line). README.md's "Risk
  scoring methodology" section rewritten to document this as the one rule
  that applies everywhere risk history is shown, not just describe the old
  (inconsistent) sparkline-specific rendering choice. Verified via a
  simulated `HISTORY` array with a deliberate gap (5, absent, 7): popup
  sparkline now plots 2 points not 3, and Compare's trend still reads
  RISING (Δ2) — same conclusion, not diluted by a fake 0.
- **Deep-link `?tab=analyst` bug fixed**: `applyDeepLink()` was calling
  `marker.openPopup()` and only *then* registering
  `map.once("popupopen", ...)` to auto-click the Analyst tab. Leaflet fires
  `popupopen` synchronously from inside `openPopup()`, so the listener was
  always registered one event too late — the tab switch silently never
  fired on first load. Reproduced against the pre-fix code with Playwright
  (`analystTabActive: false`) before fixing, confirmed fixed after
  (`analystTabActive: true`). Fix: register the `map.once("popupopen", ...)`
  listener *before* calling `marker.openPopup()`. Public URL format
  (`?country=<name>&tab=<news|analyst|analysis>`) unchanged.
- **UK coat-of-arms attribution added**: the CC BY-SA 3.0/GFDL requirement
  flagged in NOTICE.md since 2026-08-06 was still unresolved. Added one line
  to the existing footer `.credits` strip on both index.html and
  analyst.html: "UK Royal Coat of Arms (HM Government) by Sodacan, CC BY-SA
  3.0 — all other emblems public domain (see NOTICE.md)", linking to the
  Commons file page. Author name and license version confirmed live against
  the file page's own licensing section before writing the credit line (not
  guessed). No new UI chrome — reuses the existing footer.
- **Printable Analyst Brief (index.html)**: unchanged this session, and
  reverified still works exactly as before (brief visible, map/cards/
  filters/nav/print-button hidden, banner still visible) after the other
  print-media changes landed in analyst.html — the two pages' print CSS
  don't interact.

## Files changed this session
`analyst.html` (print/copy-link controls: CSS, markup, JS), `index.html`
(sparkline missing-value fix + comment, deep-link listener ordering fix, UK
attribution footer line), `README.md` (risk scoring methodology section
rewritten), `NOTICE.md` (UK attribution item marked resolved). No content
inside any existing analyst note was touched. `docs/PROJECT_STATE.md` (this
file).

## Known limitations / unfinished pieces
- Country/region keyword classification is still headline-only word-boundary
  matching — documented crudeness, not solved (pre-existing, out of scope
  this session).
- Maritime EEZ overlay: still investigated-not-built, see NOTICE.md
  (pre-existing, out of scope this session).
- The print/copy-link controls were verified with real Playwright browser
  automation this session (installed Chromium via `npx playwright install`
  since none was present) — 42 automated checks plus a real generated PDF
  (3 pages, `printBackground: true`) and a mobile-viewport screenshot, not
  just static CSS reasoning. `poppler`/`pdftoppm` wasn't available (no
  `brew` on this machine) so the PDF's rendered pixels weren't visually
  eyeballed page-by-page — page count, `printBackground`, and per-element
  computed-style visibility in `@media print` were all checked
  programmatically instead, which is a stronger signal than eyeballing for
  this class of bug but isn't literally the same as a human looking at the
  PDF.
- All work this session is uncommitted in the working tree — user's
  standing rule is they review before anything goes to git, and this
  session was explicitly told not to commit or push.

## Next logical step
User review of the diff (`analyst.html`, `index.html`, `README.md`,
`NOTICE.md`). If they want the PDF actually eyeballed pixel-by-pixel,
install poppler (`brew install poppler` — brew itself wasn't present on
this machine either) or open `analyst.html` in a real browser and use
Print Preview directly. Commit only on explicit request, matching this
project's established "commit locally, review, then push" pattern.
