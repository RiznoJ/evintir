# EVINTIR — PROJECT ROADMAP

A staged execution plan for building a public-source strategic monitoring
platform, structured as a sequence of milestones with defined scope,
deliverables, and proof of completion. Built and executed independently,
with AI tooling used selectively for research, debugging, and technical
review — consistent with the project's stated methodology.

**Operating principles:**
1. Sequential execution — one milestone completed before the next begins.
2. Every work session concludes with a commit and a corresponding
   learning-log entry documenting what was built and what was learned.
3. Technical blockers are treated as debugging exercises: isolate the
   error, research it, and resolve it — escalating to AI assistance only
   after independent troubleshooting.

---

## TOOLCHAIN

| Tool | Role | Environment |
|---|---|---|
| GitHub | Repository hosting and version history | Browser |
| GitHub Pages | Static site hosting for the live dashboard | Browser (config) |
| GitHub Actions | Scheduled automation for the RSS data pipeline | Browser (config) |
| Python | Data ingestion and classification pipeline | Local |
| Git (CLI) | Version control, local-to-remote workflow | Local |
| VS Code | Development environment | Local |
| Claude Code | AI-assisted development support | Local |

Development began entirely in-browser; local tooling was introduced once
foundational structure was in place, deliberately sequencing complexity.

---

## MILESTONE 0 — Baseline review

**Objective:** Understand the starting architecture before modifying it.
**Deliverable:** A working understanding of the event schema and why a
static file preview shows placeholder data absent a live server.
**Proof:** Documented in the first learning-log entry.

## MILESTONE 1 — Initial deployment

**Objective:** Establish a live, publicly accessible instance with an
automated data-refresh pipeline.
**Deliverable:** Live URL; GitHub Actions successfully committing fetched
data on a recurring schedule.
**Proof:** Live site + initial commit history.

## MILESTONE 2 — Documentation infrastructure

**Objective:** Establish a running technical log as both a development
record and a public artifact of process.
**Deliverable:** `learning-log.md` initialized and versioned.
**Proof:** File present with entries for Milestones 0–1.

## MILESTONE 3 — Customization and ownership

**Objective:** Move the project from template to original work — naming,
visual identity, data sources, and copy — via a series of discrete,
well-documented commits.
**Scope (minimum four):**
- Rebrand: naming, visual identity, repository name
- Design tokens: establish accent color scheme via CSS variables
- Data sources: add and validate an additional public RSS feed
- Classification: tune region/category matching rules
- Copy: rewrite README framing in project voice
**Proof:** Commit history demonstrating iterative, single-purpose changes —
the standard expected of professional version control practice.

## MILESTONE 4 — Local execution environment

**Objective:** Run the full data pipeline independently, outside the
GitHub-hosted automation.
**Deliverable:** Local server operational; pipeline script executed
manually with observed output.
**Proof:** Learning-log entry with supporting screenshot.

## MILESTONE 5 — Version control fluency

**Objective:** Transition from browser-based editing to a full local
git workflow — clone, edit, stage, commit, push.
**Deliverable:** A commit originating from local git, not the GitHub web
editor.
**Proof:** Commit history reflecting the workflow change.

## MILESTONE 6 — Technical deep dives

**Objective:** Systematically build fluency in the project's underlying
technical concepts through structured, self-directed sessions:

1. Event schema design and field rationale
2. HTML/CSS/JavaScript separation of concerns
3. State-to-render flow (filter interactions)
4. Asynchronous data loading via fetch() and JSON
5. The Python ingestion pipeline (feedparser, classification logic)
6. CI/CD automation via GitHub Actions
7. Geospatial rendering with Leaflet
8. Risk scoring methodology and its limitations

**Method:** Each session targets one concept, using the project's actual
codebase as the working example, concluding with the concept restated
independently.
**Proof:** One learning-log entry per concept — a running technical
record, public and timestamped.

## MILESTONE 7 — Analytical layer (primary differentiator)

**Objective:** Apply an analyst's discipline on top of automated
collection — the component that distinguishes this project from a
standard news aggregator.
**Recurring process:**
1. Review the highest-risk auto-ingested events from the live dashboard.
2. Cross-verify against a second independent public source.
3. Author dated analyst briefs — executive summary, key developments,
   significance, confidence level, open questions — as a distinct,
   version-controlled artifact separate from the automated feed.
4. Iterate the underlying methodology over time: move from a keyword-based
   placeholder toward a documented, defensible risk rubric.
**Proof:** A growing, dated body of analyst work — the artifact most
directly relevant to demonstrating independent judgment and tradecraft.

## MILESTONE 8 — Finalization

- Live-site documentation (screenshots, README) for portfolio presentation
- README retrospective, written independently and reviewed for accuracy
- Resume framing finalized
- Optional refinements: map animation, "what changed" delta view

---

## USE OF AI ASSISTANCE

AI tools are used selectively: as a research aid for troubleshooting,
as a technical reviewer for code and writing, and as a sounding board for
design decisions — never as the source of the project's analytical
judgment or strategic direction. Model selection is matched to task
complexity: lighter-weight assistance for routine debugging and research,
heavier-weight assistance reserved for multi-file changes or substantial
new features. This division of labor is documented transparently
throughout the project's commit history and learning log.

---

## STATUS TRACKING

Progress is tracked against the milestone sequence above. Current status
and next steps are maintained in `learning-log.md`.
