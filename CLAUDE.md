# Claude Code Operating Notes — Evintir

## State tracking
Before starting work, read docs/PROJECT_STATE.md if it exists.
After any meaningful change, update it with:
- What now works that didn't before
- Files changed
- Known limitations / unfinished pieces
- The next logical step
Keep it short — bullets, not prose. Overwrite stale entries instead of appending forever.

## Verification
Never say a task is complete without actually running the check.
- JS changes: run `node --check`
- Data changes: confirm the JSON parses
- If a check wasn't run, say so — don't assume it passed.

## Scope
Match existing patterns (see countries.js, data/notes.json schema) instead of inventing new ones.
Don't add dependencies unless there's no reasonable way around it.
Don't touch files outside what the task asked for.
