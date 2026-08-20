# Tech Watch

A filterable index of defense-technology developments drawn from three
YouTube channels, covering 28 February 2026 (start of the 2026 Iran war)
forward. **Tech Watch is the collection layer, not the analysis layer** —
see the distinction below before anything else.

## Collection, not analysis

Tech Watch and Analyst Notes are visibly and structurally separate on
purpose:

| | Tech Watch | Analyst Notes |
|---|---|---|
| What it is | An auto-drafted index of what public videos discuss | Hand-written assessment with confidence labels |
| How entries are made | Clustered from video titles, blurb drafted from an auto-caption transcript, reviewed before publish | Written by hand, sourced and cited |
| What a blurb claims | "Covers reported...", "Discusses..." — a claim about the *videos* | A claim about the *world*, with a stated confidence level |
| Data file | `data/techwatch.json` | `data/notes.json` |

Tech Watch entries never get treated as verified facts and never feed into
`data/notes.json` or the Analyst Notes tab. If something in Tech Watch
turns out to matter, it gets written up properly, by hand, as its own
Analyst Note — Tech Watch never substitutes for that step.

## The three channels

| Channel | Tier | Why |
|---|---|---|
| Sandboxx | secondary | Defense reporting and commentary, broadest topical range of the three. Claims are leads requiring primary-source confirmation. |
| Cappy Army | secondary | Veteran-hosted defense commentary. Same secondary-source caveat. |
| DARPAtv | primary | Official DARPA channel — a primary source for DARPA program statements. |

Every published entry labels each linked video "primary source" or
"secondary source" so a reader can weigh it accordingly. See
`config/techwatch.json` for the channel IDs and tier notes.

## Why detection runs in CI but extraction runs locally

Two very different jobs, split for a concrete reason:

- **Detection** (`scripts/watch_channels.py`, runs in CI on a 6-hour cron,
  `.github/workflows/techwatch.yml`) — polls each channel's public YouTube
  RSS feed (`/feeds/videos.xml?channel_id=...`). Standard library only,
  no dependencies, no API key, no yt-dlp. Cheap and safe to run
  unattended on a GitHub-hosted runner.
- **Extraction** (`scripts/index_channels.py` for the historical backfill,
  `scripts/fetch_representatives.py` for transcripts) — uses `yt-dlp`,
  which YouTube actively blocks from datacenter IP ranges (including
  GitHub Actions runners). This has to run from a residential IP, i.e.
  locally, by hand.

RSS also only returns a channel's ~15 most recent uploads, which is enough
for ongoing detection but nowhere near enough for the historical backfill —
that gap is exactly why `index_channels.py` (flat-playlist listing, no
download) exists as a separate, locally-run script.

## The 28 Feb 2026 floor date

`config/techwatch.json`'s `floor_date` (2026-02-28) marks the start of the
2026 Iran war and is the scope boundary for the whole feed. It's an
absolute floor, never relaxed — videos published before it are never
indexed, clustered, or published, regardless of topic relevance.

## Status lifecycle

Each video in `data/watchlist.json` moves through:

```
indexed -> clustered -> transcribed -> used
```

with terminal states `irrelevant`, `no_captions`, `needs_date` at whichever
point they apply. Each cluster in `data/clusters_draft.json` has its own
independent status: `draft` -> `approved` | `rejected`.

## Closed vocabularies

`topics` (13 categories) and `theaters` (5 regions) in
`config/techwatch.json` are **closed vocabularies** — nothing anywhere in
the pipeline may invent a tag outside them. `scripts/draft_blurbs.py`
validates every API response's `theaters` against the list and discards
the response (recording an error, never publishing an invented tag) if it
doesn't match exactly.

## Why clusters, not videos

Roughly 170 source videos collapse into a few dozen clusters because the
three channels frequently cover the same underlying development. A reader
does not need three near-identical headlines about the same interceptor
test — they need one entry with one blurb and every source video linked
underneath it, each labeled with its own channel and source tier.
`scripts/build_clusters.py` groups relevant videos by topic + a rolling
time window (`cluster_window_days`) and only ever transcribes one
representative video per cluster (chosen by `representative_priority`,
Sandboxx > Cappy Army > DARPAtv, tie-broken by earliest publish date) —
never every video in the cluster.

## The approve-before-publish gate

Nothing publishes automatically. `build_clusters.py` only ever produces
`status: "draft"` clusters. A human sets `status: "approved"` in
`data/clusters_draft.json` by hand (or `"rejected"` to discard it
permanently — rejected clusters are frozen exactly like approved ones and
never regenerated). `scripts/publish_techwatch.py` is the only script that
writes the public `data/techwatch.json`, and it only ever includes
clusters that are both `approved` and have a non-empty headline and blurb.
An approved cluster still missing a blurb is skipped and reported, not
silently published half-finished.

## Why transcripts are gitignored

`sources/transcripts/` holds full-text captions of third-party YouTube
videos. The repo is public, and committing full transcripts would be a
redistribution problem — the site publishes short blurbs and links, never
the underlying caption text itself, so the transcripts have no reason to
leave the local machine that generated them.

## On blurbs and analysis

Every Tech Watch blurb is drafted from an auto-generated caption transcript
of exactly one representative video, describes what that video (and the
cluster's other linked videos) *discuss*, and is reviewed by a human before
`status` is ever set to `approved`. A blurb is never a verified factual
claim and never an analytical assessment — auto-captions reliably corrupt
proper nouns, program names, and numbers, so `scripts/draft_blurbs.py`'s
prompt explicitly forbids specific figures and instructs the model to
describe unfamiliar names generically rather than guess a spelling. All
analytical content anywhere on this site — confidence-labeled assessments,
open questions, sourced reporting — lives in Analyst Notes and is written
by hand, never generated.

## Run order

One-time (or occasional) historical backfill, plus each pipeline pass
after it:

```bash
python3 scripts/index_channels.py --dry-run      # verify counts
python3 scripts/index_channels.py                # one time, free
python3 scripts/build_clusters.py                # free, no API
# review data/clusters_draft.json, set status: "approved" on the clusters you want
python3 scripts/fetch_representatives.py --limit 10
python3 scripts/draft_blurbs.py --limit 10        # ~10 API calls, pennies
# review/edit headlines and blurbs, set human_edited: true where you rewrote
python3 scripts/publish_techwatch.py
```

Ongoing, after the CI-run `watch_channels.py` has added new rows to
`data/watchlist.json`:

```bash
git pull
python3 scripts/build_clusters.py
# review new draft clusters, approve the ones worth publishing
python3 scripts/fetch_representatives.py && python3 scripts/draft_blurbs.py
python3 scripts/publish_techwatch.py
```

`scripts/draft_blurbs.py --no-api` skips the API step entirely and prints
a checklist of clusters awaiting a hand-written blurb, so the whole
pipeline can run at zero cost if preferred.
