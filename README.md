# TidalTools

A small Python toolkit for keeping a Tidal "My Music" library organized into genre/era/culture
**category playlists**. The recurring job it automates: **whenever you favorite new songs, work
out which category each belongs in and add it to that playlist** — without ever touching your
existing playlists or favorites.

The genre judgement for each new song is made by an **AI agent** following a documented runbook,
so re-running this is fast and requires no code edits. There are no API keys to manage (Tidal
auth is interactive; MusicBrainz needs none).

## Layout

```
auth.py          one-time Tidal login (OAuth device flow) -> session.json
fetch.py         pull favorites + playlists from Tidal     -> data/playlists.json
classify.py      build the worklist of new, unplaced songs -> data/unclassified.json
                 (also (re)writes data/classification.json)
apply.py         add classified tracks to their playlists on Tidal (additive, idempotent)
enrich.py        optional: MusicBrainz genre tags          -> data/genres.json
analyze.py       optional: advisory regrouping report       -> data/report.md
common.py        shared paths + Tidal session load/save
data/            classification.json (tracked) + caches (gitignored)
docs/            CATEGORIES.md (taxonomy) + CLASSIFY_RUNBOOK.md (agent steps)
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python auth.py                  # opens a link.tidal.com URL to approve in your browser
```

`auth.py` saves OAuth tokens to `session.json`. **`session.json` is a secret** (it grants full
account access) and is gitignored — never commit it. Tokens auto-refresh; if a session goes
stale, just run `python auth.py` again.

## The workflow (adding newly favorited songs)

```bash
python fetch.py            # 1. refresh the local snapshot of your library
python classify.py         # 2. list the new songs that aren't in any category yet
#                            3. an agent assigns each one (see docs/CLASSIFY_RUNBOOK.md)
python classify.py         # 4. re-run to confirm the worklist is now empty
python apply.py            # 5. dry run: shows exactly what would be added
python apply.py --commit   # 6. add the new tracks to their category playlists on Tidal
python fetch.py            # 7. refresh the snapshot to reflect the new state
```

Step 3 is the only manual/agent step. To do it, an agent reads `data/unclassified.json` plus
[`docs/CATEGORIES.md`](docs/CATEGORIES.md) and edits
[`data/classification.json`](data/classification.json) per
[`docs/CLASSIFY_RUNBOOK.md`](docs/CLASSIFY_RUNBOOK.md). If a song fits none of the categories,
the agent flags it and asks before creating a new one.

## Safety model

- **Additive & idempotent.** `apply.py` only *adds* tracks that aren't already in a playlist.
  Re-running it changes nothing. It never removes or reorders tracks.
- **My Music is never modified.** Categories are copies of favorites; your favorites stay intact.
- **Dry run by default.** `apply.py` makes no changes without `--commit`, and after committing it
  re-reads each playlist from Tidal to confirm the adds landed.

## Optional: genre tags

`python enrich.py` looks up MusicBrainz genre tags per artist (no API key; rate-limited) into
`data/genres.json`. `classify.py` folds these into the worklist as hints, and `analyze.py` can
produce an advisory regrouping report (`data/report.md`). Neither is required for the workflow.

## Git / secrets

`.gitignore` excludes `session.json` (secret), the regenerable library cache
(`data/playlists.json`, `data/genres.json`, `data/report.md`), scratch dumps (`data/_*.txt`),
`.venv/`, and bytecode. The taxonomy and the song→category mapping (`data/classification.json`)
are tracked so an agent can pick up and redo the triage from a fresh clone. See
`session.json.example` for the expected token file shape.
