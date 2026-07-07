## July 7 — Went live
- Got Evintir live on GitHub Pages (riznoj.github.io/evintir).
- Set up the GitHub Actions robot to pull public RSS every 6 hours.
- Renamed the project from WATCHSTANDER to Evintir by editing index.html.
- Learned: repos, commits, folders vs files, why index.html must sit at the root, and the difference between a warning I can ignore and an error I must fix.
- Hard part: hidden dot-files and folder nesting (had to redo the upload once).
- What clicked: the whole pipeline — public feeds → fetch_feeds.py → data/events.json → the dashboard.
