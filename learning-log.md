## July 7 — Went live
- Got Evintir live on GitHub Pages (riznoj.github.io/evintir).
- Set up the GitHub Actions robot to pull public RSS every 6 hours.
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
## August 7 — North Korea and Japan Analyst Notes, deployment troubleshooting
- What I did: Wrote two long-form Analyst Notes — North Korea's compute/sensing modernization (missile tests as the visible layer over a less visible push for AI-equipped drones, satellite reconnaissance, and GPU acquisition through barter, alignment, and theft) and Japan's institutional buildout of a more sovereign national-security architecture (a new centralized intelligence bureau, the shift from manned aircraft to drones, and the Rapidus semiconductor program, read as one coordinated move rather than four separate stories) — then had Claude Code convert both into the site's actual post schema and publish them.
- Technical notes:
  - Schema fidelity mattered more than speed here: before touching notes.json, had Claude Code confirm the real field structure against an already-published Deep Analysis post (Russia's "Volume War," Aug 5) rather than trust the schema I'd sketched out ahead of time. The real pattern splits a post into `reporting` (single flowing paragraph), `analysis` (multi-paragraph, the actual assessment), `confidence`, and `openQuestion` (also single paragraph) — not the three even sections I'd drafted around. Sourced Reporting and Open Questions each collapsed into one dense paragraph as a result; every sentence is intact, just not visually paragraph-broken the way Assessment is. Worth fixing the render layer for that eventually, not tonight.
  - Verification was scripted, not eyeballed: wrote a script that diffed all 22 source URLs (12 for North Korea, 10 for Japan) against the list I'd supplied, character for character, before calling it done — catching a transcription error at that stage is a lot cheaper than catching it after a board member clicks a broken citation.
  - Both countries already had emblem badges and NOTICE.md license entries from yesterday's attribution audit, so today was purely a content/schema exercise, not new infrastructure. Confirmed the badges actually activate (not just that the JSON is valid) by simulating the site's own `activeCountries()` function against the live data file.
  - Neither country has matching RSS coverage yet — none of the five feeds in the pipeline are North Korea- or Japan-specific — so both map badges currently show the "no event data" grey state and an empty News tab. Left that as-is rather than faking coverage; it's an honest gap, and the next feed-expansion pass (NK News, NHK World, Nikkei Asia were already on my candidate list) closes it for real.
  - Deployment hiccup: after pushing, GitHub Pages sat queued for several minutes with no progress — turned out to be a stuck run, not a bad push. Re-running the wrong job the first time (an old automated data-refresh run instead of the one blocking my actual changes) taught me to check the commit message tied to a run, not just its position in the list. An empty trigger commit forced a clean new deployment once I understood what was actually stuck.
- What I learned: The schema-fidelity discipline from this session is the same lesson as August 5's Deep Analysis posts, just sharper — I had a format in my head before I'd looked at the real file, and the real file was right, my assumption wasn't. Checking first cost five minutes; publishing on the wrong assumption would have cost a rewrite. Also: verifying a citation list programmatically catches what my own eyes would eventually miss on the twenty-second URL.
- Site state: 13 posts across 10 countries, 4 tagged Deep Analysis (Russia, China, North Korea, Japan).
- Commit(s): https://github.com/RiznoJ/evintir/commits/main
## August 10 — Built a YouTube transcript pipeline, shipped two Deep Analysis posts, fixed a badge bug
- What I did: Built a transcript-pulling pipeline from scratch so I can pull raw source material from public defense channels (DARPA's official channel, defense-analysis creators) without ever touching video files — captions only. Tested it deliberately before trusting it: ran it on a single video first, read the output line by line, and only pointed it at more videos once the format was clean. Used the pipeline's output as the starting material for two new Deep Analysis posts — the Pentagon's UAP file disclosures, and Ukraine's balloon-decoy campaign against Russian air defense, with DARPA's Lift Challenge as the structural counterpoint in the second piece. Also caught and fixed a real bug in the US country badge that's apparently been live since the badge system went in.
- Technical steps:
  - Wrote sources/fetch_transcript.sh around yt-dlp. Hit a wall immediately — yt-dlp's default extraction is currently broken against YouTube (a known "page needs to be reloaded" failure on their end, not mine). Fixed it with --extractor-args "youtube:player_client=android" — a flag yt-dlp already supports, not a new dependency. Deliberately avoided a third-party wrapper repo I found (Agent-Reach) that does something similar — vetted it first, decided the "point an agent at a raw URL and let it install itself" pattern wasn't something I wanted near a public intel project, even though the underlying tool (yt-dlp) checked out fine.
  - Script pulls captions only (--skip-download), prefers human captions and falls back to auto-generated (detected by checking info.json's subtitles vs automatic_captions keys), and deletes every intermediate .vtt/.info.json so only finished .md transcripts stick around.
  - Ran the script on one video first and stopped there on purpose — I wanted to see the actual output before scaling up, not assume the spec I wrote was right. Good thing I did: the first pass exposed a formatting bug I hadn't anticipated. Auto-caption cues break mid-sentence, so a naive "strip timestamps and dedupe" pass left choppy one-clause-per-line text — technically matched what I asked for, useless to actually read. Rewrote the cleanup step to rejoin fragments into real sentences and paragraph-group them, re-tested on that same video to confirm the fix, and only then ran it on the remaining three.
  - Ended up with 4 transcripts total (3 DARPA, 1 defense-analysis channel) in sources/transcripts/.
  - Once I had real transcript text instead of just a topic in my head, I switched over to my planning chat (separate from Claude Code) and had it do the actual research pass — cross-checking every claim in the transcripts against primary reporting, catching where the source material overstated or conflated things, and pulling the real program specs, dates, and figures that turned raw video transcripts into something citable. That's the split I'm sticking with going forward: Claude Code touches files and runs scripts; the planning chat does research, fact-checking, and drafting. Keeping research out of Claude Code specifically also means it's not burning tool calls re-fetching the same sources over and over.
  - For sourcing the two articles: I'd drafted both with a "Source notes" section naming outlets but no actual URLs. Had Claude Code go find and verify a real link for every citation instead of guessing or inventing one, then re-check each surviving URL. A few didn't survive — one citation turned out to be about the wrong country's balloons, one outlet's coverage never actually turned up, dropped both rather than force them in.
  - Coat-of-arms bug: the US badge has been showing the wrong SVG — a plain striped shield instead of the full eagle-and-shield design every other country's badge uses. Caught it by actually rendering the SVG instead of trusting the filename. Swapped to the correct Commons file.
- What broke / caught in verification: One source citation (a DOE/PANTEX nuclear-facility file mentioned in the UAP article) was originally misattributed to the fifth release batch — verification traced it to the fourth batch instead, since the actual fifth-batch source doesn't mention DOE/PANTEX at all. Corrected the batch number in the published note and double-checked the fix against two independent passes (a live web-research check plus my own direct source verification) before calling it settled.
- What I learned (plain English): A tool breaking against its default path isn't automatically a "go find a new tool" problem — yt-dlp already had a working alternate route built in, I just had to use it instead of reaching for something new. The bigger lesson was about process, not code: testing on one video before scaling to a whole channel is what caught the caption-formatting bug while it only cost me one wasted file instead of dozens. And keeping research separate from execution — planning chat does the fact-checking, Claude Code just touches files — turned out to matter for more than just organization; it's also what kept Claude Code from burning tool calls re-fetching sources on its own initiative.
- What I learned (analytical): Both pieces circle the same underlying idea — the gap between what's publicly known and what the defense-tech frontier actually holds, and the discipline of holding multiple explanations at once instead of reaching for the most dramatic one. Full reasoning is in the articles themselves.
- Site state: 15 posts across 11 countries, 6 tagged Deep Analysis. sources/transcripts/ now holds 4 pulled transcripts. US coat-of-arms badge corrected.
- Commit(s): https://github.com/RiznoJ/evintir/commits/main