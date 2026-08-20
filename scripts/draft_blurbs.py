"""
=============================================================================
draft_blurbs.py — Tech Watch: the only script that costs money
=============================================================================
WHAT THIS SCRIPT DOES: for clusters whose representative video has been
  transcribed, sends the transcript to Claude (one call per CLUSTER, never
  per video) and asks for a plain-index headline/blurb/theaters triple —
  never analysis, never asserted facts (see the hardcoded prompt below).

  --no-api mode leaves every blurb empty and prints a checklist so the whole
  project can run at zero cost with hand-written blurbs instead.

  Uses stdlib urllib for the API call rather than the anthropic SDK, to
  avoid adding a dependency (this repo's only external library is
  feedparser, per requirements.txt).

WHO RUNS IT: you, manually, after fetch_representatives.py has produced
  transcripts. Costs a small amount per run (Haiku, capped output tokens).
=============================================================================
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from techwatch_common import REPO_ROOT, load_config, load_watchlist, load_clusters_draft, save_clusters_draft

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 400
API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
SLEEP_SECONDS = 1
RETRY_DELAY_SECONDS = 10
TRUNCATE_HEAD = 12000
TRUNCATE_TAIL = 2000

PROMPT_TEMPLATE = """You are generating descriptive index metadata for a public OSINT reference site. You are NOT writing analysis, assessment, or commentary.

INPUT is an auto-generated YouTube caption transcript. Auto-captions reliably corrupt proper nouns, program names, acronyms, and numbers. Treat every specific detail as unreliable.

Return ONLY a JSON object, no preamble and no markdown fences:
{{"headline": string, "blurb": string, "theaters": [string]}}

RULES:

1. The blurb describes WHAT THE SOURCE VIDEOS COVER. It is a claim about the videos, never a claim about the world. Write "Covers reported...", "Discusses...", "Walks through...". Never write "X has achieved Y" or any assertion of fact.

2. Include NO specific figures: no dollar amounts, no quantities, no dates, no ranges, no speeds, no unit designations. Auto-captions corrupt these and they must not appear.

3. If a system or program name appears but you are not confident of its exact spelling, describe it generically. "a new counter-drone interceptor" beats a misspelled program name.

4. No superlatives, no promotional language. Banned: revolutionary, game-changing, unprecedented, groundbreaking, stunning, massive, terrifying.

5. headline: under 90 characters, sentence case, plainly descriptive, not clickbait, not a copy of the video's title.

6. blurb: one or two sentences, under 320 characters.

7. theaters: 0 to 3 items chosen ONLY from this list, copied exactly:
{theaters_list}
Use "Homeland & Global" for US-domestic or non-theater-specific items.

TOPIC (already assigned, for context only): {topic}
This entry covers {n} videos published between {date_start} and {date_end}.

TRANSCRIPT OF REPRESENTATIVE VIDEO:
{transcript}
"""


def load_dotenv():
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def eligible_clusters(clusters_data, watchlist):
    out = []
    for c in clusters_data["clusters"]:
        if c["status"] not in ("draft", "approved"):
            continue
        if c.get("human_edited"):
            continue
        if c["blurb"]:
            continue
        rep = watchlist["videos"].get(c["representative_video_id"])
        if not rep or rep.get("status") != "transcribed" or not rep.get("transcript_path"):
            continue
        out.append(c)
    return out


def load_transcript_text(transcript_path):
    p = Path(transcript_path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p.read_text(encoding="utf-8", errors="replace")


def truncate_transcript(text, head=TRUNCATE_HEAD, tail=TRUNCATE_TAIL):
    if len(text) <= head + tail:
        return text
    return text[:head] + "\n\n...[transcript truncated]...\n\n" + text[-tail:]


def call_api_once(api_key, prompt):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, e
    except urllib.error.URLError as e:
        return None, e


def call_api_with_transport_retry(api_key, prompt):
    """Exactly one retry, after 10s, on 429/5xx. No unbounded retry."""
    data, err = call_api_once(api_key, prompt)
    if err is None:
        return data, None
    status = getattr(err, "code", None)
    if status == 429 or (status is not None and 500 <= status < 600):
        time.sleep(RETRY_DELAY_SECONDS)
        data, err = call_api_once(api_key, prompt)
        if err is None:
            return data, None
    return None, str(err)


def parse_model_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```\s*$", "", text).strip()
    return json.loads(text)


def draft_for_cluster(cluster, transcript_text, config, api_key):
    theaters_allowed = set(config["theaters"])
    prompt = PROMPT_TEMPLATE.format(
        theaters_list=json.dumps(config["theaters"]),
        topic=cluster["topic"],
        n=len(cluster["videos"]),
        date_start=cluster["date_start"],
        date_end=cluster["date_end"],
        transcript=truncate_transcript(transcript_text),
    )

    last_error = "unknown error"
    for attempt in range(2):  # one initial attempt + one validation retry
        data, err = call_api_with_transport_retry(api_key, prompt)
        if err:
            return None, err
        try:
            text = data["content"][0]["text"]
            parsed = parse_model_json(text)
            headline = parsed["headline"]
            blurb = parsed["blurb"]
            theaters = parsed.get("theaters", [])
            if not isinstance(headline, str) or not isinstance(blurb, str):
                raise ValueError("headline/blurb not strings")
            if not isinstance(theaters, list) or any(t not in theaters_allowed for t in theaters):
                raise ValueError(f"theater outside allowed vocabulary: {theaters}")
            return {"headline": headline.strip(), "blurb": blurb.strip(), "theaters": theaters}, None
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            last_error = f"response validation failed: {exc}"
            continue

    return None, last_error


def main():
    parser = argparse.ArgumentParser(description="Draft Tech Watch cluster headlines/blurbs via Claude.")
    parser.add_argument("--no-api", action="store_true",
                         help="Skip API calls; print a checklist of clusters awaiting a hand-written blurb.")
    parser.add_argument("--limit", type=int, default=10, help="Max clusters to process this run (default 10).")
    parser.add_argument("--cluster-id", help="Only process this cluster.")
    parser.add_argument("--dry-run", action="store_true", help="Print how many API calls would be made, call nothing.")
    args = parser.parse_args()

    config = load_config()
    watchlist = load_watchlist()
    clusters_data = load_clusters_draft()

    candidates = eligible_clusters(clusters_data, watchlist)
    if args.cluster_id:
        candidates = [c for c in candidates if c["cluster_id"] == args.cluster_id]

    if args.no_api:
        print(f"{len(candidates)} cluster(s) awaiting a hand-written blurb:")
        for c in candidates:
            print(f"  [{c['cluster_id']}] topic={c['topic']} rep={c['representative_video_id']} "
                  f"suggested_headline={c['suggested_headline']!r}")
        print("\n--no-api: no API calls made, no files written. "
              "Edit headline/blurb by hand and set human_edited: true.")
        return

    candidates = candidates[: args.limit]

    if args.dry_run:
        print(f"--dry-run: would make {len(candidates)} API call(s), one per cluster:")
        for c in candidates:
            print(f"  [{c['cluster_id']}]")
        return

    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set (checked .env and environment). "
              "Use --no-api to draft blurbs by hand at zero cost instead.", file=sys.stderr)
        sys.exit(1)

    processed = 0
    for c in candidates:
        rep = watchlist["videos"][c["representative_video_id"]]
        print(f"[{c['cluster_id']}] drafting from {rep['transcript_path']}")
        try:
            transcript_text = load_transcript_text(rep["transcript_path"])
        except OSError as exc:
            c["error"] = f"could not read transcript: {exc}"
            print(f"  ERROR: {c['error']}")
            save_clusters_draft(clusters_data)
            continue

        result, err = draft_for_cluster(c, transcript_text, config, api_key)
        if err:
            c["error"] = err
            print(f"  ERROR: {err}")
        else:
            c["headline"] = result["headline"]
            c["blurb"] = result["blurb"]
            c["theaters"] = result["theaters"]
            c["error"] = None
            print(f"  headline: {result['headline']}")

        processed += 1
        save_clusters_draft(clusters_data)
        time.sleep(SLEEP_SECONDS)

    print(f"\nDone. Processed {processed} cluster(s). Wrote data/clusters_draft.json")


if __name__ == "__main__":
    main()
