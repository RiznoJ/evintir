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