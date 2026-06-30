"""Add classified tracks to their category playlists on Tidal (additive, idempotent).

Reads data/classification.json (built by classify.py + an agent; see
docs/CLASSIFY_RUNBOOK.md) and ensures each category playlist on Tidal contains the
tracks assigned to it. It ONLY adds missing tracks:

  - Never removes tracks, never reorders, never touches "My Music" (favorites).
  - Creates a category playlist only if it does not exist yet.
  - Re-reads each playlist back from Tidal to confirm the adds landed.

Safe to re-run: tracks already present are skipped, so a second run is a no-op.

  python apply.py            dry run  (uses the local cache; shows what would be added)
  python apply.py --commit   actually creates playlists / adds tracks on Tidal
"""
from __future__ import annotations

import json
import sys

from common import CLASSIFICATION_FILE, PLAYLISTS_FILE, load_session

PLAYLIST_DESC = "Auto-categorized from My Music"
MY_MUSIC = "My Music"


def load_assignments() -> dict[str, list[dict]]:
    if not CLASSIFICATION_FILE.exists():
        raise SystemExit("No data/classification.json. Run:  python classify.py  first.")
    data = json.loads(CLASSIFICATION_FILE.read_text(encoding="utf-8"))
    assignments = data.get("assignments") or {}
    if not assignments:
        raise SystemExit("classification.json has no assignments. Run classify.py.")
    return assignments


def cached_category_ids() -> dict[str, set[str]]:
    """{category -> set(track id)} from the last fetch (local cache), excluding My Music."""
    if not PLAYLISTS_FILE.exists():
        return {}
    out: dict[str, set[str]] = {}
    for p in json.loads(PLAYLISTS_FILE.read_text(encoding="utf-8")):
        if p["name"] == MY_MUSIC:
            continue
        out[p["name"]] = {str(t["id"]) for t in p["tracks"] if t.get("id") is not None}
    return out


def build_plan(assignments, current):
    """Return {category -> [(id, title), ...]} of assigned tracks not already present."""
    plan: dict[str, list[tuple[str, str]]] = {}
    for cat, rows in assignments.items():
        have = current.get(cat, set())
        to_add = [
            (str(r["id"]), r.get("title"))
            for r in rows
            if r.get("id") is not None and str(r["id"]) not in have
        ]
        if to_add:
            plan[cat] = to_add
    return plan


def main() -> None:
    commit = "--commit" in sys.argv
    assignments = load_assignments()
    cached = cached_category_ids()
    plan = build_plan(assignments, cached)
    new_cats = [c for c in plan if c not in cached]

    print("=== PLAN (additive; My Music never touched) ===")
    for cat, to_add in plan.items():
        tag = "CREATE" if cat not in cached else "exists"
        print(f"  [{tag}] '{cat}': +{len(to_add)} to add")
        for _, title in to_add:
            print(f"        + {title}")
    total = sum(len(v) for v in plan.values())
    if new_cats:
        print(f"  New categories to create: {new_cats}")

    if total == 0:
        print("\nNothing to do - Tidal already matches the classification. (idempotent)")
        return

    if not commit:
        extra = f" and create {len(new_cats)} playlist(s)" if new_cats else ""
        print(f"\n[DRY RUN] Would add {total} track(s){extra}. Re-run with --commit to apply.")
        return

    session = load_session()
    existing = {pl.name: pl for pl in session.user.playlists()}

    print("\n=== APPLYING ===")
    for cat, to_add in plan.items():
        pl = existing.get(cat)
        if pl is None:
            pl = session.user.create_playlist(cat, PLAYLIST_DESC)
            existing[cat] = pl
            print(f"  [CREATED] '{cat}'")
        # Recompute against fresh server state (the local cache may be stale).
        server_ids = {str(t.id) for t in pl.tracks(limit=10000)} if pl.num_tracks else set()
        ids = [i for (i, _) in to_add if i not in server_ids]
        if not ids:
            print(f"  [skip] '{cat}': already up to date")
            continue
        for i in range(0, len(ids), 100):  # Tidal add limit
            pl.add(ids[i:i + 100])
        after = {str(t.id) for t in pl.tracks(limit=10000)}
        missing = [i for i in ids if i not in after]
        status = "OK" if not missing else f"MISMATCH missing={missing}"
        print(f"  [{status}] '{cat}': +{len(ids)} added, playlist now has {len(after)}")

    print("\nDone. My Music untouched. Re-run  python fetch.py  to refresh the cache.")


if __name__ == "__main__":
    main()
