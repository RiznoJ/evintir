## July 7 — Went live
- Got Evintir live on GitHub Pages (riznoj.github.io/evintir).
- Set up the GitHub Actions robot to pull public RSS every 6 hours.
- Renamed the project from WATCHSTANDER to Evintir by editing index.html.
- Learned: repos, commits, folders vs files, why index.html must sit at the root, and the difference between a warning I can ignore and an error I must fix.
- Hard part: hidden dot-files and folder nesting (had to redo the upload once).
- What clicked: the whole pipeline — public feeds → fetch_feeds.py → data/events.json → the dashboard.
## July 14 — Analyst tab, country badges, map upgrades
- What I did: Set up local development for the first time — cloned the
  repo to my Desktop, ran a local Python server (`python3 -m http.server`)
  so I could preview changes instantly instead of waiting on GitHub Pages.
  Directed Claude Code (running inside VS Code, with direct file access to
  my project) through a multi-file build: a new Analyst Notes page, a
  country-badge lookup system, and map upgrades (clustering, legend, pulse
  animation, chokepoint markers). Reviewed the design tradeoffs myself
  before building — decided to use flags-style coat-of-arms badges sourced
  from Wikimedia Commons instead of a fixed country list, decided posts
  should be tagged by country rather than region so the site scales as I
  write more. Wrote and edited 4 Analyst posts myself (Iran, Russia, China,
  US), fact-checking my own claims against real sources before publishing
  any of them.
- Technical steps I ran: `cd` into the right project folder (kept
  accidentally running the server from Desktop instead of the repo —
  learned to always check my current directory first), started/stopped
  the local server with `python3 -m http.server` (had to kill a stuck
  process with Ctrl+C once), used `git add .`, `git commit -m "..."`, and
  `git push` to publish changes to GitHub Pages.
- What broke / confused me: Kept starting the terminal in the wrong folder
  at first. Also learned my event data only tags broad regions, not
  individual countries, so the map's country "News" tabs are more accurate
  for some countries than others right now — a real limitation I now know
  to design around instead of overselling in interviews.
- What I learned (plain English): The difference between data (notes.json)
  and code (the HTML/JS that renders it) — I can now add new Analyst posts
  myself just by editing one JSON file, no code changes needed. Local
  preview + git push is a much faster loop than the GitHub web editor.
- Commit(s): https://github.com/RiznoJ/evintir/commits/main
## August 3 — Long-form analyst posts, two new countries, date sorting

- What I did: Wrote three new Analyst posts (Russia, Ukraine, Israel) and lit up the
  Ukraine and Israel country badges. Extended the post schema with a longer free-form
  "analysis" body field, updated the render layer to display it, and added
  date-based sorting (default newest-first) with a newest/oldest toggle that composes
  with the existing country filter.

- Technical notes:
  - Schema change (data/notes.json): appended posts p5-p7 to the posts array,
    preserving all existing entries including the Iran placeholder (p1). Added a new
    optional "analysis" field alongside the existing reporting / assessment /
    confidence / openQuestion fields. Paragraph breaks inside analysis are stored as
    escaped \n in the JSON string. Validated the file parses cleanly after edit —
    a single trailing comma or unescaped quote in those long fields breaks the whole
    load, so JSON validity was the key check.
  - Render layer (analyst.html): the analysis field only appears if it renders it,
    so I had it read the field and inject a paragraph block between the assessment
    and confidence sections, splitting on \n so each paragraph is its own element.
    This is the data-vs-presentation split in practice — adding the field to the data
    does nothing until the code that reads the data is updated to handle it.
  - Country badges (countries.js): confirmed Ukraine and Israel keys resolve to the
    Wikimedia Special:FilePath redirect (Coat_of_Arms_of_Ukraine.svg,
    Emblem_of_Israel.svg) — the redirect pattern avoids needing the file's MD5 hash.
    Badges are generated dynamically from which countries have posts, so no separate
    list needed updating — writing the post is what creates the badge.
  - Sort feature (analyst.html): the non-trivial part. Sort has to act on the
    already-filtered set, so country filter and sort toggle both read/write the same
    view state instead of overwriting each other. Sorted on the date field
    (descending by default); toggle flips the comparator without touching the active
    country filter.
  - Local verification: ran the local Python server, checked badge generation, post
    rendering, the analysis field display, and the filter+sort combination
    (e.g. "Russia + oldest first" shows only Russia, reordered) before pushing.

- What I learned (technical): The recurring lesson is the separation between data and
  the code that presents it — the analysis field and the sort both required touching
  the render layer, not just the JSON. The sort was a small lesson in shared state:
  two independent controls (filter, sort) have to operate on one view model or they
  fight each other.

- What I learned (analytical): High-level analysis comes from anticipating a sharp
  reader's objections and handling them inside the post, then labeling what can't be
  resolved. Strongest posts turn the argument on themselves (the Russia post ends by
  asking whether external pressure strengthens the regime rather than cracking it).
  Built Russia and Ukraine as a linked pair, each pointing at the other's central
  uncertainty. Kept the public-sources-only rule strict — raised
  intelligence/surveillance questions as open questions grounded in public facts
  rather than asserting classified capability.

- Site state: 7 posts across 6 countries (US, China, Russia x2, Ukraine, Israel) plus
  the Iran placeholder. Next: convert the Iran placeholder into a real post.

- Commit(s): https://github.com/RiznoJ/evintir/commits/main
## August 4 — UK and France briefs, workflow fix
- Added UK and France to the 22-country system, one analyst brief each.
- Workflow fix: realized I'd never run /clear in Claude Code, so every run was re-scanning months of context and burning usage. New split — desktop app for drafting/reasoning, Claude Code for mechanical execution only, /clear before each batch. Draft everything in the app, then paste one consolidated payload into a clean Code session.
- Model split: higher-reasoning model for analyst writing (confidence calibration, catching advocacy-vs-analysis), faster model for mechanical edits and git. Match model to task, not habit.
- Briefs: UK — the specialization/integration bet (Palantir, Defence Investment Plan, offshore-balancer history) vs. its historic instinct to stand apart. France — Gaullist autonomy carried by the nuclear deterrent (Île Longue forward deterrence) vs. an eroding economic base. Structurally mirrored, each stands alone in its own section.
- Next: Iran post, About page, instructions-doc update.
## August 5 — Deep Analysis tier, two long-form info-ops posts, nav rename
- What I did: Wrote a two-part Deep Analysis series — Russia's "volume war" (firehose-of-falsehood disinformation, Doppelganger, the Pravda/Portal Kombat LLM-grooming network) and China's "consensus forgery" (Spamouflage/Dragonbridge, coordinated-inauthentic-behavior detection shifting from content to network graphs). Both go well past my normal post length, so I needed a way to visually flag them as a heavier tier before a reader commits to reading.
- Schema/render decisions: Didn't add a new field for the tier. The existing `tag` string already drove a badge (`.keytag`), so I extended the render logic to derive a CSS class straight from the tag's text — same pattern `.conf-Medium-Low` already used for confidence — so `tag: "DEEP ANALYSIS"` gets `.keytag-DEEP-ANALYSIS`, an outlined-brass variant instead of solid, with zero new JSON fields. Also collapsed each post's three source-doc confidence axes (state attribution / objective / effectiveness) down into the one `confidence` field the schema supports, keeping the other two reasoned out in prose inside `analysis` instead of silently dropping them.
- Nav fix: "Analyst" → "Analysis" in the top nav on both pages — was bugging me grammatically every time I looked at it. Left the page title, the "Analyst Notes" subtitle, and the map popup's internal News/Analyst toggle alone; those are separate labels, not the nav bar.
- Verification: `node --check` on the touched inline script (extracted analyst.html's `<script>` block to check it, since `node --check` doesn't parse HTML directly), confirmed notes.json still parses with Python's json module after appending ~1,500 words of new post content, then served the site locally to eyeball the badge contrast and post rendering before pushing.
- What I learned: A single field can carry more than one concern if the render layer derives structure from its value instead of a human picking a class — same idea as the confidence badges, just applied one component over. Also relearned that translating a richly-structured source document into a flatter schema means making explicit calls about what gets folded into prose vs. what gets cut, rather than quietly losing detail.
- Site state: 11 posts across 8 countries, 2 of them tagged Deep Analysis.
- Commit(s): https://github.com/RiznoJ/evintir/commits/main
## August 6 — News-relevance fix, five new features, attribution audit, maritime overlay
- What I did: Came in with a big list from a planning session and worked it top to bottom in one sitting instead of picking one thing — set the scope, then directed Claude Code through all of it: fixed the real bug where a country's News tab was showing unrelated world news (region was too coarse; events now get tagged with the actual countries mentioned in the headline), then built five features I'd scoped out — a per-feed freshness indicator, a risk trend sparkline per country, a two-country compare view, a printable Analyst Brief, and a shareable deep link — plus a NOTICE.md attribution audit and a shipping-lanes map overlay. Made the calls on how far to push it (everything, not just the one fix) and how to ship it (commit locally after each piece, don't push until I'd reviewed) before eventually deciding to trust the batch and push without reading every diff myself — a real tradeoff between velocity and review discipline that I made consciously, not by accident.
- Technical notes:
  - News-tab fix: the actual bug was in how `countries.js` mapped events to countries — most non-Middle-East/Russia-Ukraine/US countries fell back to one giant "Global" region bucket, so e.g. Japan's News tab was really "recent Global news," not Japan news. Fix was tagging events with the specific countries mentioned at ingest time (`fetch_feeds.py`) instead of relying on that bucket, with a real empty state when a country has no current coverage instead of quietly falling back to the unfiltered feed.
  - Also had Claude Code escape every place RSS-derived text gets inserted into the page — that data comes from external sites I don't control, so treating it as trusted HTML was a real gap, not a hypothetical one.
  - Freshness/sparkline/compare/print/deep-link: each shipped with its own reasoning documented in the commit history — the sparkline formula in particular is written out plainly in the README now (category severity × recency decay, capped at 10) because a trend chart with a hidden formula isn't something I'd trust from someone else's project either.
  - Attribution audit turned up a real finding, not just paperwork: the UK coat-of-arms file on Wikimedia Commons is CC BY-SA, not public domain like the other 21 — needs a proper attribution line I don't have yet. Logged as an open item instead of quietly fixed, so it doesn't get lost.
  - Maritime overlay: shipped the shipping-lanes layer (small, CC BY 4.0, clearly labeled as a static 2012 CIA reference source, not live ship tracking), but held off on the EEZ boundary layer after the numbers came back — even a version scoped to just my tracked countries would have meant a 40+ MB data file. Better to not ship something that would slow the site down than to force a feature in because it was on the list.
  - Deploy hit a real git conflict: the GitHub Actions cron had pushed four automated data refreshes while I was working. Merged them in rather than force-pushing over them, kept my schema changes, and re-ran the pipeline once more right before going live so the data is both current and has the new fields the UI needs.
- What I learned: The biggest lesson today wasn't technical — it was about how much review a change actually needs before it goes live, and being honest with myself (and in this log) about when I skipped that step. A portfolio project meant to demonstrate judgment isn't well served by a journal that hides the tradeoffs I actually made.
- Site state: news filtering, freshness, sparkline, compare view, print, and deep-link all live; shipping lanes overlay live; EEZ layer deliberately not shipped yet.
- Commit(s): https://github.com/RiznoJ/evintir/commits/main