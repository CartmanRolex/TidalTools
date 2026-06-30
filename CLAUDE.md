# CLAUDE.md — agent guide for TidalTools

TidalTools keeps a Tidal "My Music" library sorted into genre **category playlists**. Your job
as an agent is the one step that needs judgement: **classify newly favorited songs into the
right category.** Everything else is scripted.

## The loop
```
python fetch.py        # snapshot library -> data/playlists.json
python classify.py     # -> data/unclassified.json  (the new songs needing a category)
#  >> YOU classify them here: edit data/classification.json (see docs/CLASSIFY_RUNBOOK.md)
python classify.py     # confirm it prints "Worklist empty"
python apply.py        # dry run, review the plan
python apply.py --commit   # add tracks to Tidal (additive; confirm with the user first)
python fetch.py        # refresh the snapshot
```

## To classify (the only manual step)
1. Read `data/unclassified.json` (the worklist) and `docs/CATEGORIES.md` (the taxonomy).
2. Assign each song to one category by editing **`data/classification.json`** — append
   `{"id", "title", "artist"}` to the right list under `"assignments"`. Full steps + schema:
   **`docs/CLASSIFY_RUNBOOK.md`**.
3. If a song fits none of the categories: mark it an outlier, OR (if several new songs form a
   clear new cluster) **propose a new category and ask the user before creating it**.

## Invariants (never break)
- **Never modify "My Music" / favorites.** Categories are copies; favorites stay intact.
- Assign by **track `id`**, never by row/position.
- `apply.py` is **additive & idempotent** — it only adds missing tracks, never removes/reorders.
  Re-running it is a no-op. It's dry-run unless `--commit` is passed.
- Category names in `classification.json` must exactly match the Tidal playlist names listed in
  `docs/CATEGORIES.md`.
- **`session.json` is a secret** (OAuth tokens) — never commit it or print its contents. If Tidal
  auth fails, ask the user to run `python auth.py` (interactive browser login).

## Files
- Code: `auth.py`, `fetch.py`, `classify.py`, `apply.py`, `enrich.py`, `analyze.py`, `common.py`
- Data: `data/classification.json` (source of truth, tracked); `data/playlists.json`,
  `data/genres.json`, `data/unclassified.json` (regenerable caches, gitignored)
- Docs: `README.md`, `docs/CATEGORIES.md`, `docs/CLASSIFY_RUNBOOK.md`
