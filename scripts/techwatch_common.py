"""
Shared helpers for the Tech Watch pipeline:
index_channels.py, build_clusters.py, fetch_representatives.py,
draft_blurbs.py, publish_techwatch.py, watch_channels.py.

Kept separate from fetch_feeds.py's one-file-per-job pattern because these
six scripts share the same config file, the same watchlist/clusters JSON
files, and the same yt-dlp resolution logic — duplicating that six times
would be the actual maintenance risk.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "techwatch.json"
WATCHLIST_PATH = REPO_ROOT / "data" / "watchlist.json"
CLUSTERS_DRAFT_PATH = REPO_ROOT / "data" / "clusters_draft.json"
TECHWATCH_OUT_PATH = REPO_ROOT / "data" / "techwatch.json"

# Mirrors sources/fetch_transcript.sh's own fallback: this project's yt-dlp
# isn't on PATH in the dev shell, so both that script and this one check the
# same known pip --user install location before giving up.
YTDLP_FALLBACK = Path.home() / "Library" / "Python" / "3.9" / "bin" / "yt-dlp"


def utcnow_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def load_watchlist():
    if WATCHLIST_PATH.exists():
        with open(WATCHLIST_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"generated_utc": "", "videos": {}}


def save_watchlist(data):
    data["generated_utc"] = utcnow_iso()
    _write_json(WATCHLIST_PATH, data)


def load_clusters_draft():
    if CLUSTERS_DRAFT_PATH.exists():
        with open(CLUSTERS_DRAFT_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"generated_utc": "", "clusters": []}


def save_clusters_draft(data):
    data["generated_utc"] = utcnow_iso()
    _write_json(CLUSTERS_DRAFT_PATH, data)


def save_json_techwatch(data):
    data["generated_utc"] = utcnow_iso()
    _write_json(TECHWATCH_OUT_PATH, data)


def resolve_ytdlp():
    """Prefer PATH, fall back to the known pip --user install location —
    identical resolution order to sources/fetch_transcript.sh."""
    on_path = shutil.which("yt-dlp")
    if on_path:
        return on_path
    if YTDLP_FALLBACK.exists():
        return str(YTDLP_FALLBACK)
    raise RuntimeError(f"yt-dlp not found on PATH or at {YTDLP_FALLBACK}")


def yyyymmdd_to_iso(raw):
    """'20260304' -> '2026-03-04'; anything else -> None."""
    if not raw or len(raw) != 8 or not raw.isdigit():
        return None
    return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
