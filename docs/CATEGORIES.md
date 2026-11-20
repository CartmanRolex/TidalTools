# Category taxonomy

These are the canonical genre/era/culture categories the Tidal library is organized into.
Each category is a real playlist on Tidal. **The category name here must match the Tidal
playlist name exactly** (these are the ASCII forms — note the hyphen `-`, not an em dash).

This file is the source of truth for *what each category means*. The actual song→category
mapping lives in [`../data/classification.json`](../data/classification.json).

| Category (exact playlist name) | What goes here | Example artists |
|---|---|---|
| **80s & Retro Pop** | Synth-pop, Euro-disco, new wave, NDW, 80s pop. The biggest cluster. | Alphaville, Modern Talking, OMD, Bad Boys Blue, Bonnie Tyler, Madness |
| **Classic Rock & Oldies** | 60s–70s rock & oldies. | The Who, The Turtles, The Animals, Iggy Pop, The Mamas & The Papas |
| **Modern Rock, Pop & Indie** | Alt-rock, indie, and contemporary pop (90s–today). | Radiohead, Måneskin, RHCP, MGMT, Mitski, Dua Lipa, Portishead |
| **Latin - Cumbia, Salsa & Tropical** | Cumbia, salsa, vallenato, Andean and electro-tropical. | Fruko Y Sus Tesos, Grupo Soñador, Chicha Libre, Bomba Estéreo |
| **Latin - Pop, Folk & Ballads** | Latin pop, rancheras, boleros, folk and ballads. | Shakira, Los Angeles Negros, Bronco, Jeanette, Onda Vaga, Karol G |
| **Brazilian - Funk & MPB** | Brazilian funk, baile, and MPB (incl. ex-Brazil tracks). | MC Kevinho, Carrapicho, Vanessa Da Mata, Trinix (BR collabs) |
| **Reggae & Dub** | Reggae and dub. | Stick Figure, Max Romeo, Big Mountain, Biga Ranx |
| **House, Dance & Electronic** | Tech-house, deep house, synthwave, club remixes/mashups. | FISHER, Bakermat, Kavinsky, Shouse, Riordan |
| **World - Africa & Middle East** | Arabic/raï, Levantine pop/indie, West/Central African. | Amr Diab, Rachid Taha, Cheikh Lô, Mashrou' Leila, Aziz Maraka |
| **World - Slavic, Caucasus & Asia** | Russian, Turkish, Armenian/Georgian, bhangra, Uzbek & Central-Asian pop. | Катя Лель, Sertab, Panjabi MC, Dilnoz, Mandili, Ladaniva |

## Rules

- **Pick exactly one** category per song — the one that best matches its dominant genre/era/style.
- **Era beats nationality** for Western pop/rock: a 1983 synth-pop song goes in *80s & Retro Pop*,
  not in a country bucket. The Latin/Brazilian/World buckets are for non-Western genres where the
  cultural style *is* the defining trait.
- **Outliers**: a song that genuinely fits none of these (e.g. a classical piece) is left only in
  *My Music* with no category. Record it under `outliers` in `classification.json` so it is not
  flagged again. There is currently one outlier: *Beethoven — Symphony No. 7 (Allegretto)*.
- **New categories**: only when several recent additions form a clear cluster that fits none of the
  10 above (e.g. a batch of jazz or hip-hop). **Propose it and ask the user before creating it.**
  See [`CLASSIFY_RUNBOOK.md`](CLASSIFY_RUNBOOK.md).
