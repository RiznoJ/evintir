# WATCHSTANDER PLAYBOOK — your master roadmap

This is the high-level map. You work ONE milestone at a time, in order.
Every milestone tells you: what you're doing, WHERE you do it, what to paste
into Claude (Opus) if you want click-by-click babysitting, what "done" looks
like, and what PROOF it leaves behind.

**The three rules:**
1. One milestone at a time. Never skip ahead.
2. Every work session ends with a commit and a learning-log entry (even two sentences).
3. Stuck more than 20 minutes? Copy the exact error message into Opus. Reading
   errors and asking precise questions IS the skill.

---

## THE TOOL MAP (read once, refer back forever)

| Tool | What it is | Where | When you need it |
|---|---|---|---|
| GitHub (website) | Stores + publishes your project | Browser | Milestone 1, forever |
| GitHub Pages | Free hosting — makes the repo a live site | Browser (a settings switch) | Milestone 1 |
| GitHub Actions | Free robot that runs your Python script every 6h | Browser (a settings switch) | Milestone 1 |
| GitHub web editor | Edit files right on the website | Browser | Milestones 2–3 |
| Python | Runs the data pipeline (fetch_feeds.py) | Your computer (later) | Milestone 4 |
| git (command line) | Professional way to save/upload changes | Your computer | Milestone 5 |
| VS Code | A text editor (optional but nice) | Your computer | Milestone 5+ |
| Claude Code | AI assistant in your terminal | Your computer | Milestone 6+ |

Download nothing until Milestone 4. Milestones 1–3 are 100% browser.

---

## MILESTONE 0 — Look at what you have (15 min, today)

**Where:** your computer, no accounts needed.
**Do:** unzip `watchstander-v2.zip`. Open `index.html` by double-clicking —
you'll see the map with 2 fallback events (that's expected; the full data
needs a server — explained in the file's comments). Skim the comments at the
top of `index.html` and `scripts/fetch_feeds.py`. Don't try to understand
everything.
**Done when:** you can answer, in your own words, in one sentence each:
(a) what does `data/events.json` do, and (b) why does double-clicking show
only 2 events?
**Proof:** write both answers down — they become your first learning-log entry.

## MILESTONE 1 — Get it live on GitHub (~30–40 min)

**Where:** browser only.
**Do:** follow `docs/SETUP_GUIDE.md` steps 1–6 exactly. End state: a live URL
and a working data robot.
**Paste into Opus if stuck:**
> "I'm following a setup guide to put a dashboard project on GitHub. I'm on
> the step where [describe step]. Here's what I see on my screen: [describe
> or screenshot]. Walk me through just this step, one click at a time."
**Done when:** your live URL shows the dashboard, and the Actions tab shows a
green check that committed real headlines into `data/events.json`.
**Proof:** the live URL + a commit history with your first commits.

## MILESTONE 2 — Start the learning log (~20 min)

**Where:** browser (GitHub web editor) — this milestone secretly teaches you
how to create and commit a file.
**Do:** in your repo: Add file → Create new file → name it
`docs/learning-log.md` → paste the template below → commit with message
`docs: start learning log`.

```markdown
# Learning Log

## 2026-07-XX — Project went live
- What I did:
- What broke / confused me:
- What I learned (plain English):
- Commit(s): [paste link to the commit]
```

**Every session from now on adds one entry.** This file is your proof of
learning AND your Obsidian-style notes, kept where interviewers can see them.
**Done when:** the file exists with your Milestone 0 + 1 entries in it.

## MILESTONE 3 — Make it yours (the ad-lib milestone) (~1–2 hrs, can split)

**Where:** browser (GitHub web editor). Each change = its OWN commit with a
clear message. Small commits are professional; giant ones are amateur.

Pick from this menu — do at least four:

- [ ] **Rename it.** WATCHSTANDER is a placeholder. Pick your name — change it
      in `index.html` (the wordmark + title), `README.md`, and the repo name
      (Settings → General → Rename).
      Commit: `feat: rename project to ____`
- [ ] **Recolor it.** In `index.html`, find `:root` in the CSS. Change
      `--brass: #C9A44C;` to any hex color (Google "color picker"). One line
      changes the whole accent scheme — that's design tokens at work.
      Commit: `style: change accent color`
- [ ] **Add a news feed.** In `scripts/fetch_feeds.py`, copy one FEEDS entry
      and point it at another public RSS feed you care about. Ask Opus:
      "Find me a reliable public RSS feed for [topic] and check the URL
      works." Commit: `feat: add ____ RSS feed`
- [ ] **Tune the regions.** Edit REGION_RULES keywords to match your focus
      (e.g., add more Israel-related terms). Commit: `feat: tune region rules`
- [ ] **Rewrite the README intro** in your own voice. Commit: `docs: rewrite intro`
- [ ] **Change the banner text** if you want different wording.

**Done when:** ≥4 commits, each one thing, each with a message that says what
and why. **Proof:** your commit history now shows iteration — exactly what
reviewers look for.

## MILESTONE 4 — Run it on your own machine (~1 hr)

**Where:** your computer. First download: Python (python.org — check "Add to
PATH" when installing).
**Do:** SETUP_GUIDE step 7 (local server), then run the pipeline yourself:
`pip install -r requirements.txt` → `python scripts/fetch_feeds.py` → watch
it print each feed → refresh your local page and see the data change.
**Paste into Opus:** "Walk me through installing Python on [Windows/Mac] and
running a local web server for my project, step by step. I've never used a
terminal."
**Done when:** you ran the script yourself and understand the print output.
**Proof:** learning-log entry + screenshot saved to `docs/`.

## MILESTONE 5 — Learn real git (~1–2 hrs)

**Where:** your computer. Downloads: git (git-scm.com), VS Code (optional).
**Do:** clone your repo, change one small thing in VS Code, then
`git add` → `git commit` → `git push`. One full cycle, done by hand.
**Paste into Opus:** "Teach me to clone my GitHub repo, make one change, and
push it back, explaining every command before I run it. I'm on [OS]."
**Done when:** a commit in your history was made from your machine, not the
web editor. From here on, prefer the command line.

## MILESTONE 6 — The teardown sessions (ongoing, 8 short sessions)

**Where:** Claude (Opus is fine — one concept per chat keeps it cheap).
This is your backwards-learning phase, done properly. One session each:

1. The event schema — why every field exists
2. HTML vs CSS vs JavaScript — the three languages in index.html
3. State → render: what happens when you click a filter
4. fetch() and JSON: how the dashboard loads data
5. The Python pipeline: feedparser, classify(), and the "reports/port" bug
6. GitHub Actions: read update-feeds.yml line by line
7. Leaflet: how the map and markers work
8. The risk rubric and confidence labels — and their limitations

**Session format (paste into Opus):**
> "Open my project file [name]. Teach me concept #N from my playbook using MY
> actual code. Quiz me at the end with 3 questions. Don't move on until I can
> explain it back in my own words."

**Proof:** after each session, write the concept in your own words in the
learning log. Those 8 entries ARE your Obsidian vault, public and timestamped.

## MILESTONE 7 — The analyst layer (your actual edge) (~ongoing, weekly)

**Where:** browser or VS Code. This is where your analytics background shows.
**Do — weekly watch routine (30 min):**
1. Open your live dashboard. Pick the 3–5 highest-risk auto-ingested events.
2. Verify each against a second public source.
3. Edit `data/events.json` manually is NOT the way (the robot overwrites it) —
   instead keep `docs/weekly-brief-YYYY-MM-DD.md`: executive summary, key
   developments, why it matters, confidence, what to watch. Your dashboard
   collects; YOU analyze. Commit each brief.
4. Later upgrade (ask Fable when ready): a reviewed-events file the robot
   merges instead of overwriting, and a documented risk rubric to replace the
   keyword placeholder.
**Proof:** a growing folder of dated analyst briefs — the single most
Navy/CWO-relevant artifact in the whole project.

## MILESTONE 8 — Polish + the fun stuff (~2–3 hrs)

- [ ] Screenshot of the live site in the README
- [ ] Write "What I learned" in README — your own words, reviewed by Opus for
      accuracy, not written by it
- [ ] Finalize the resume bullet (you have a draft in your project brief)
- [ ] **The radar sweep** 🎯 — the cosmetic you asked about. Ask Fable:
      "Add a subtle radar-sweep animation to my dashboard map, and explain
      how the CSS animation works." It's ~20 lines. You earned it by now.
- [ ] Optional: "What changed today" delta panel (ask Fable)

---

## WHICH CLAUDE FOR WHAT

- **Opus (default — save your credits):** click-by-click walkthroughs, error
  messages, teardown sessions, explaining commands, reviewing your log
  entries, finding RSS feeds, git lessons.
- **Fable (rare — heavy builds only):** new features touching multiple files
  (reviewed-events merge, delta panel, radar sweep, big refactors).
- Same Project, same files — just switch the model dropdown.

## IF YOU GET LOST

Come back to this file. Find your current milestone. Do the next unchecked
box. That's it — the whole project is never bigger than the next checkbox.
