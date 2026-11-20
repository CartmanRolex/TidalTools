# Classification runbook (for an AI agent)

This is the step-by-step an agent follows to triage **newly added** "My Music" songs into the
existing category playlists. This is the only step that needs judgement — everything else is
scripted. Goal: every new favorite ends up assigned to a category (or recorded as an outlier).

## Inputs
- **`../data/unclassified.json`** — the worklist: songs in My Music not yet in any category.
  Each entry has `id`, `title`, `artist`, `year`, `bpm`, `key`, and `genre_tags` (MusicBrainz
  tags, only if `enrich.py` has been run — may be empty).
- **`CATEGORIES.md`** — the taxonomy: the 10 categories, what each means, and the rules.
- **`../data/genres.json`** *(optional)* — MusicBrainz artist→tags; already merged into the
  worklist's `genre_tags`. Run `python enrich.py` first if you want these as a hint.

## Steps
1. **Run `python classify.py`** to (re)generate `unclassified.json`. If it prints
   "Worklist empty", there is nothing to do — stop.
2. **For each song in `unclassified.json`**, decide its category using `CATEGORIES.md`
   (title + artist + year + tags). Use your own music knowledge; `genre_tags` is only a hint.
   - Fits one of the 10 → assign it there.
   - Fits none, and it's a one-off oddity (e.g. classical) → mark it an **outlier**.
   - Fits none, but several new songs form a clear new cluster → **stop and ask the user**
     whether to create a new category (give the proposed name + the songs). Do not invent a
     category unilaterally. Leave such songs in My Music until the user decides.
3. **Edit `../data/classification.json`** (do not edit any `.py` file):
   - To assign a song: append `{"id": <id>, "title": "...", "artist": "..."}` to the right list
     under `"assignments"`. Copy `id`/`title`/`artist` straight from the worklist entry.
   - To mark an outlier: append `{"id": <id>, "title": "...", "artist": "...", "note": "why"}`
     to `"outliers"`.
   - For an approved new category: add a new key under `"assignments"` whose name will become
     the new Tidal playlist name (follow the naming style in `CATEGORIES.md`), then add the
     category to `CATEGORIES.md`.
4. **Run `python classify.py` again** to confirm it prints "Worklist empty". (It re-reads the
   file and keeps your assignments even though they aren't on Tidal yet.)
5. **Hand back to `apply.py`** — see the workflow in [`../README.md`](../README.md):
   `python apply.py` (dry run) → confirm → `python apply.py --commit`.

## `classification.json` shape
```json
{
  "version": 1,
  "outliers": [
    {"id": 12345, "title": "Symphony No. 7 (Allegretto)", "artist": "London Symphony Orchestra",
     "note": "classical, stays in My Music"}
  ],
  "assignments": {
    "80s & Retro Pop": [
      {"id": 67890, "title": "Big in Japan", "artist": "Alphaville"}
    ],
    "Reggae & Dub": [
      {"id": 11111, "title": "Sound of the Sea", "artist": "Stick Figure"}
    ]
  }
}
```

## Invariants (do not break)
- Assign by **track `id`** (stable), never by position/row number.
- **Never** modify "My Music" / favorites, and never remove or reorder existing tracks.
- One category per song.
- Category names in `classification.json` must exactly equal the Tidal playlist names in
  `CATEGORIES.md`.
