# Ten Fifty Bakers × NWTRS — Festival Promo Video

A 3:05 promotional film for the North West Trail Running Series (Tasmanian Film
Festival screening), introducing Ten Fifty Bakers — 1,100 acres and 23 km of
private trails at Bakers Beach, Tasmania — ahead of the property joining the
2027 series.

## Deliverable

`TenFifty_NWTRS_Promo.mp4` — 1920×1080, 24 fps, H.264 + AAC, 3:05.
Soundtrack: `Verse 1.mp3` (repo root).

## Structure (cut to the song's energy map)

| Time | Act | Content |
|------|-----|---------|
| 0:00–0:10 | Open | Drone wide over bush to the coast, title |
| 0:10–0:24 | The land | Aerials, gate sign — "1,100 private acres / 23 km of wild trails" |
| 0:24–0:48 | The trails | Forest tracks, creek triptych, misty valleys, kangaroo |
| 0:48–1:10 | Trail climax | Hilltop coast POV, plains walkers, sunset firepit aerial |
| 1:10–1:18 | House reveal | "Then come home to Ten Fifty" |
| 1:18–2:06 | The house | Interiors, food, sauna, outdoor baths, firepit circle |
| 2:06–2:33 | Night payoff | Sunset/moon AI motion, real aurora photos AI-animated |
| 2:33–3:05 | Cards | NWTRS 2027 welcome, offer, booking, logo |

## Offer (as shown on cards)

- For NWTRS runners, friends & family
- Stay 2 nights — 3rd night free · Stay 3 nights — 4th night free
- Book by midnight Sunday, stay any time in the next 12 months
- tenfiftybakers.com.au · code **NWTRS**

## Pipeline

- `build.py` — EDL + segment renderer (beat-snapped cuts from `aubiotrack`
  analysis of the song; Ken Burns for stills; portrait creek videos as a
  triptych; phone footage gets a mild grade)
- `cards.sh` — end-card design (Montserrat + brand gold `#CCB268`)
- `assemble.py` — concat, crossfades at act boundaries, 12 title overlays,
  audio mux
- AI motion: 4 stills animated via Kling 3.0 image-to-video (two aurora
  timelapses, drifting sunset clouds, moonlit sky), upscaled to 2K
- Source assets: Dropbox (`BAKERS`, `Photos for NWTRS 8-26`, `Jonah`)
