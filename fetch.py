"""Pull all playlists + tracks from Tidal into data/playlists.json (read-only)."""
from __future__ import annotations

import json
from datetime import datetime

from common import PLAYLISTS_FILE, load_session

PAGE = 100  # tracks per request


def _year(track) -> int | None:
    album = getattr(track, "album", None)
    if album is not None:
        y = getattr(album, "year", None)
        if y:
            return int(y)
    rel = getattr(track, "tidal_release_date", None)
    if isinstance(rel, datetime):
        return rel.year
    return None


def _track_record(track, playlist_name: str) -> dict:
    artists = [a.name for a in (getattr(track, "artists", None) or []) if getattr(a, "name", None)]
    if not artists and getattr(track, "artist", None):
        artists = [track.artist.name]
    album = getattr(track, "album", None)
    added = getattr(track, "user_date_added", None) or getattr(track, "date_added", None)
    return {
        "id": getattr(track, "id", None),
        "title": getattr(track, "name", None) or getattr(track, "full_name", None),
        "artists": artists,
        "album": getattr(album, "name", None) if album else None,
        "year": _year(track),
        "duration": getattr(track, "duration", None),  # seconds
        "popularity": getattr(track, "popularity", None),
        "bpm": getattr(track, "bpm", None),
        "key": getattr(track, "key", None),
        "key_scale": getattr(track, "key_scale", None),
        "isrc": getattr(track, "isrc", None),
        "date_added": added.isoformat() if isinstance(added, datetime) else None,
        "playlist": playlist_name,
    }


def _all_tracks(playlist):
    """Page through a playlist's tracks, tolerant of API versions."""
    offset = 0
    while True:
        try:
            chunk = playlist.tracks(limit=PAGE, offset=offset)
        except TypeError:
            chunk = playlist.tracks()  # older signature: returns everything
            for t in chunk:
                yield t
            return
        if not chunk:
            return
        for t in chunk:
            yield t
        if len(chunk) < PAGE:
            return
        offset += PAGE


def main() -> None:
    session = load_session()

    out = []

    # "My Music" = favorited tracks collection (not a playlist in Tidal's model).
    favs = session.user.favorites.tracks(limit=10000)
    fav_records = [_track_record(t, "My Music") for t in favs]
    out.append(
        {
            "id": "favorites",
            "name": "My Music",
            "description": "Favorited tracks collection",
            "num_tracks": len(fav_records),
            "duration": sum(r["duration"] or 0 for r in fav_records),
            "created": None,
            "tracks": fav_records,
        }
    )
    print(f"My Music (favorites): {len(fav_records)} tracks")

    playlists = session.user.playlists()
    print(f"Found {len(playlists)} playlists. Fetching tracks...")

    for i, pl in enumerate(playlists, 1):
        records = [_track_record(t, pl.name) for t in _all_tracks(pl)]
        out.append(
            {
                "id": pl.id,
                "name": pl.name,
                "description": getattr(pl, "description", None),
                "num_tracks": getattr(pl, "num_tracks", None) or len(records),
                "duration": getattr(pl, "duration", None),
                "created": pl.created.isoformat() if isinstance(getattr(pl, "created", None), datetime) else None,
                "tracks": records,
            }
        )
        print(f"  [{i}/{len(playlists)}] {pl.name}: {len(records)} tracks")

    PLAYLISTS_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    total = sum(len(p["tracks"]) for p in out)
    unique = {t["id"] for p in out for t in p["tracks"] if t["id"]}
    print(f"\nDone. {len(out)} playlists, {total} tracks ({len(unique)} unique).")
    print(f"Wrote {PLAYLISTS_FILE}")
    print("Next:  python enrich.py   (optional, for genres)  then  python analyze.py")


if __name__ == "__main__":
    main()
