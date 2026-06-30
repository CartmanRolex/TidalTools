"""Build the classification snapshot and the worklist of new songs to triage.

No AI here. This script just figures out WHICH "My Music" favorites are not yet in
any category playlist (i.e. the songs you recently added) so an agent can classify
them. The actual genre judgement is made by an agent (see docs/CLASSIFY_RUNBOOK.md).

Each run:
  1. Read data/playlists.json (produced by fetch.py).
  2. Rebuild data/classification.json:
       - `assignments` {category -> [tracks]} taken from the live category playlists on
         Tidal, MERGED with any entries already in the file that aren't on Tidal yet
         (new songs an agent assigned but apply.py hasn't pushed). Tidal wins for songs
         already placed; pending agent assignments are preserved until applied.
       - `outliers` preserved as-is (songs deliberately kept only in My Music, e.g. the
         one classical piece) so they are never re-flagged.
  3. Write data/unclassified.json = My Music favorites that are in neither `assignments`
     nor `outliers` — the worklist for the agent (with metadata + genre tags if present).

Workflow:
  python fetch.py            # refresh data/playlists.json
  python classify.py         # see the worklist of newly added songs
  # agent edits data/classification.json per docs/CLASSIFY_RUNBOOK.md
  python classify.py         # confirm the worklist is now empty
  python apply.py            # dry run, then:  python apply.py --commit
"""
from __future__ import annotations

import json

from common import (
    CLASSIFICATION_FILE,
    GENRES_FILE,
    PLAYLISTS_FILE,
    UNCLASSIFIED_FILE,
)

MY_MUSIC = "My Music"


def _read_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _artist(track) -> str:
    artists = track.get("artists") or []
    if artists:
        return ", ".join(artists)
    return track.get("artist") or ""


def _slim(track) -> dict:
    return {"id": track["id"], "title": track.get("title"), "artist": _artist(track)}


def main() -> None:
    if not PLAYLISTS_FILE.exists():
        raise SystemExit("No data/playlists.json. Run:  python fetch.py  first.")

    playlists = json.loads(PLAYLISTS_FILE.read_text(encoding="utf-8"))
    by_name = {p["name"]: p for p in playlists}
    if MY_MUSIC not in by_name:
        raise SystemExit(f"'{MY_MUSIC}' not found in cache. Run fetch.py.")

    existing = _read_json(CLASSIFICATION_FILE, {})
    outliers = existing.get("outliers", [])
    outlier_ids = {str(o["id"]) for o in outliers if o.get("id") is not None}
    old_assignments = existing.get("assignments", {})

    # Live category playlists (everything except My Music) = Tidal ground truth.
    live: dict[str, list[dict]] = {}
    live_ids: set[str] = set()
    for p in playlists:
        if p["name"] == MY_MUSIC:
            continue
        rows = [_slim(t) for t in p["tracks"] if t.get("id") is not None]
        live[p["name"]] = rows
        live_ids.update(str(r["id"]) for r in rows)

    # Merge: live truth + pending entries from the file that aren't on Tidal yet
    # (new songs an agent assigned but apply.py hasn't pushed). Skip ones now on Tidal
    # or promoted to outliers.
    assignments: dict[str, list[dict]] = {cat: list(rows) for cat, rows in live.items()}
    for cat, rows in old_assignments.items():
        for r in rows:
            rid = str(r.get("id"))
            if rid in live_ids or rid in outlier_ids:
                continue
            assignments.setdefault(cat, []).append(
                {"id": r["id"], "title": r.get("title"), "artist": r.get("artist")}
            )
            live_ids.add(rid)  # treat pending as placed so it won't reappear as "new"

    classification = {"version": 1, "outliers": outliers, "assignments": assignments}
    CLASSIFICATION_FILE.write_text(
        json.dumps(classification, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    placed = {str(r["id"]) for rows in assignments.values() for r in rows} | outlier_ids

    # Worklist: My Music favorites that are not placed anywhere and not an outlier.
    genres = _read_json(GENRES_FILE, {})
    worklist = []
    for t in by_name[MY_MUSIC]["tracks"]:
        if t.get("id") is None or str(t["id"]) in placed:
            continue
        artists = t.get("artists") or []
        tags = sorted({g for a in artists for g in genres.get(a, [])})
        worklist.append(
            {
                "id": t["id"],
                "title": t.get("title"),
                "artist": _artist(t),
                "year": t.get("year"),
                "bpm": t.get("bpm"),
                "key": t.get("key"),
                "genre_tags": tags,
            }
        )
    UNCLASSIFIED_FILE.write_text(
        json.dumps(worklist, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(
        f"Categories: {len(assignments)}  |  placed tracks: {len(placed) - len(outlier_ids)}"
        f"  |  outliers: {len(outliers)}"
    )
    print(f"Wrote {CLASSIFICATION_FILE.name} and {UNCLASSIFIED_FILE.name}")
    if worklist:
        print(f"\n{len(worklist)} new song(s) to triage:")
        for w in worklist:
            yr = f" [{w['year']}]" if w.get("year") else ""
            tags = f"   tags: {', '.join(w['genre_tags'])}" if w["genre_tags"] else ""
            print(f"  - {w['title']} - {w['artist']}{yr}{tags}")
        print(
            f"\nNext: assign each in {CLASSIFICATION_FILE.name} "
            f"(see docs/CLASSIFY_RUNBOOK.md), then re-run  python classify.py"
        )
    else:
        print("\n[OK] Worklist empty - every favorite is in a category or an outlier.")
        print("Next:  python apply.py   (dry run)   then   python apply.py --commit")


if __name__ == "__main__":
    main()
