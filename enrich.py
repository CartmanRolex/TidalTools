"""Best-effort genre tags from MusicBrainz for each unique artist.

MusicBrainz has no API key but requires a descriptive User-Agent and <=1 req/sec.
Results cache to data/genres.json so re-runs only fetch missing artists.
Optional: only needed if you want genre-based regrouping suggestions.
"""
from __future__ import annotations

import json
import time

import musicbrainzngs

from common import GENRES_FILE, PLAYLISTS_FILE

musicbrainzngs.set_useragent("TidalPlaylistAnalysis", "0.1", "personal-use")


def _artist_tags(name: str) -> list[str]:
    try:
        res = musicbrainzngs.search_artists(artist=name, limit=1)
        artists = res.get("artist-list", [])
        if not artists:
            return []
        mbid = artists[0]["id"]
        detail = musicbrainzngs.get_artist_by_id(mbid, includes=["tags"])
        tags = detail["artist"].get("tag-list", [])
        tags.sort(key=lambda t: int(t.get("count", 0)), reverse=True)
        return [t["name"] for t in tags[:5]]
    except Exception as exc:  # network/lookup failures shouldn't abort the batch
        print(f"    ! {name}: {exc}")
        return []


def main() -> None:
    if not PLAYLISTS_FILE.exists():
        raise SystemExit("Run  python fetch.py  first.")

    playlists = json.loads(PLAYLISTS_FILE.read_text(encoding="utf-8"))
    artists = sorted({a for p in playlists for t in p["tracks"] for a in t["artists"]})

    cache: dict[str, list[str]] = {}
    if GENRES_FILE.exists():
        cache = json.loads(GENRES_FILE.read_text(encoding="utf-8"))

    todo = [a for a in artists if a not in cache]
    print(f"{len(artists)} unique artists, {len(todo)} need lookup (rest cached).")

    for i, name in enumerate(todo, 1):
        cache[name] = _artist_tags(name)
        print(f"  [{i}/{len(todo)}] {name}: {', '.join(cache[name]) or '(no tags)'}")
        GENRES_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        time.sleep(1.1)  # respect MusicBrainz rate limit

    print(f"\nDone. Wrote {GENRES_FILE}\nNext:  python analyze.py")


if __name__ == "__main__":
    main()
