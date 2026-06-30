"""Analyze cached playlists and emit a re-grouping report (console + data/report.md).

Read-only and advisory: nothing is written back to Tidal.
Groups/suggests along three axes — artist, era (decade), and genre (if enriched).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

from common import GENRES_FILE, PLAYLISTS_FILE, REPORT_FILE

# Heuristics for suggestions
BIG_PLAYLIST = 80        # tracks above this are "oversized" -> consider splitting
SMALL_PLAYLIST = 10      # tracks below this -> consider merging
ARTIST_CLUSTER_MIN = 8   # an artist with >= this many tracks across library -> own playlist?
GENRE_CLUSTER_MIN = 12   # a genre with >= this many tracks -> thematic playlist?


def decade(year):
    if not year:
        return "Unknown"
    return f"{(year // 10) * 10}s"


def fmt_dur(seconds):
    if not seconds:
        return "?"
    h, m = divmod(int(seconds) // 60, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m"


def load():
    if not PLAYLISTS_FILE.exists():
        raise SystemExit("Run  python fetch.py  first.")
    playlists = json.loads(PLAYLISTS_FILE.read_text(encoding="utf-8"))
    genres = {}
    if GENRES_FILE.exists():
        genres = json.loads(GENRES_FILE.read_text(encoding="utf-8"))
    return playlists, genres


def track_genres(track, genre_map):
    tags = []
    for a in track["artists"]:
        tags.extend(genre_map.get(a, []))
    return tags


def build_report(playlists, genres) -> str:
    lines: list[str] = []
    w = lines.append

    has_genre = bool(genres)
    all_tracks = [t for p in playlists for t in p["tracks"]]

    w("# Tidal Playlist Analysis & Re-grouping Suggestions\n")
    w(f"_Library: {len(playlists)} playlists, {len(all_tracks)} tracks "
      f"({len({t['id'] for t in all_tracks if t['id']})} unique)._\n")
    if not has_genre:
        w("> Genre data not available — run `python enrich.py` for genre-based "
          "suggestions. Artist/era analysis below is unaffected.\n")

    # ---- Per-playlist makeup ----
    w("\n## 1. Per-playlist makeup\n")
    for p in playlists:
        tracks = p["tracks"]
        if not tracks:
            w(f"\n### {p['name']} — _empty_\n")
            continue
        artists = Counter(a for t in tracks for a in t["artists"])
        decades = Counter(decade(t["year"]) for t in tracks)
        dur = sum(t["duration"] or 0 for t in tracks)
        top_art = ", ".join(f"{a} ({n})" for a, n in artists.most_common(5))
        dec_str = ", ".join(f"{d}: {n}" for d, n in sorted(decades.items()))
        w(f"\n### {p['name']} — {len(tracks)} tracks, {fmt_dur(dur)}\n")
        w(f"- Top artists: {top_art}\n")
        w(f"- Eras: {dec_str}\n")
        if has_genre:
            g = Counter(tag for t in tracks for tag in track_genres(t, genres))
            if g:
                w(f"- Genres: {', '.join(f'{k} ({v})' for k, v in g.most_common(5))}\n")

    # ---- Cross-playlist overlap ----
    w("\n## 2. Cross-playlist overlap (merge/dedup candidates)\n")
    track_in = defaultdict(set)
    for p in playlists:
        for t in p["tracks"]:
            if t["id"]:
                track_in[t["id"]].add(p["name"])
    dup_tracks = {tid: pls for tid, pls in track_in.items() if len(pls) > 1}
    id_to_title = {t["id"]: f"{t['title']} — {', '.join(t['artists'])}" for t in all_tracks if t["id"]}
    w(f"\n- **{len(dup_tracks)} tracks appear in 2+ playlists.**\n")
    for tid, pls in sorted(dup_tracks.items(), key=lambda kv: -len(kv[1]))[:20]:
        w(f"  - {id_to_title.get(tid, tid)} → in {len(pls)}: {', '.join(sorted(pls))}\n")

    # Artists spread across many playlists
    artist_pls = defaultdict(set)
    for p in playlists:
        for t in p["tracks"]:
            for a in t["artists"]:
                artist_pls[a].add(p["name"])
    spread = sorted(((a, pls) for a, pls in artist_pls.items() if len(pls) >= 3),
                    key=lambda kv: -len(kv[1]))
    if spread:
        w("\n- **Artists scattered across many playlists:**\n")
        for a, pls in spread[:15]:
            w(f"  - {a} → {len(pls)} playlists\n")

    # ---- Re-grouping suggestions ----
    w("\n## 3. Re-grouping suggestions\n")

    # Artist clusters
    artist_counts = Counter(a for t in all_tracks for a in t["artists"])
    big_artists = [(a, n) for a, n in artist_counts.most_common() if n >= ARTIST_CLUSTER_MIN]
    w("\n### By artist — candidates for a dedicated playlist\n")
    if big_artists:
        for a, n in big_artists:
            w(f"- **{a}** — {n} tracks across your library\n")
    else:
        w("- No single artist reaches the threshold; library is artist-diverse.\n")

    # Era buckets
    w("\n### By era — chronological split\n")
    era_counts = Counter(decade(t["year"]) for t in all_tracks)
    for d, n in sorted(era_counts.items()):
        w(f"- {d}: {n} tracks\n")

    # Genre clusters
    if has_genre:
        w("\n### By genre — thematic split\n")
        genre_counts = Counter(tag for t in all_tracks for tag in track_genres(t, genres))
        big_genres = [(g, n) for g, n in genre_counts.most_common() if n >= GENRE_CLUSTER_MIN]
        for g, n in big_genres[:20]:
            w(f"- **{g}** — {n} tracks\n")
        if not big_genres:
            w("- No genre reaches the threshold; genres are spread thin.\n")

    # Size-based housekeeping
    w("\n### Housekeeping — split big / merge small\n")
    big = [p for p in playlists if len(p["tracks"]) >= BIG_PLAYLIST]
    small = [p for p in playlists if 0 < len(p["tracks"]) <= SMALL_PLAYLIST]
    empty = [p for p in playlists if not p["tracks"]]
    for p in big:
        w(f"- **Split?** {p['name']} has {len(p['tracks'])} tracks (large).\n")
    for p in small:
        w(f"- **Merge?** {p['name']} has only {len(p['tracks'])} tracks.\n")
    for p in empty:
        w(f"- **Empty:** {p['name']} — remove or repurpose.\n")
    if not (big or small or empty):
        w("- Playlist sizes look balanced.\n")

    return "".join(lines)


def main() -> None:
    playlists, genres = load()
    report = build_report(playlists, genres)
    REPORT_FILE.write_text(report, encoding="utf-8")

    # Console: pretty if rich is available, plain otherwise.
    try:
        from rich.console import Console
        from rich.markdown import Markdown

        # legacy_windows=False avoids the cp1252 win32 console renderer.
        Console(legacy_windows=False).print(Markdown(report))
    except Exception:
        print(report)

    print(f"\n[report saved to {REPORT_FILE}]")


if __name__ == "__main__":
    main()
