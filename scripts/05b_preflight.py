"""Step 05b - inspect a raw dump BEFORE sampling or burning engine time.

Catches the two failure modes that waste a day:
  1. the time-control filter silently matching nothing (event naming differs
     by era), leaving you with an empty sample and no error
  2. a rating distribution so skewed that a band is unpopulated

Reads only the first --n games, so it is fast even on a 30GB file.

    python3 scripts/05b_preflight.py --file data/raw/lichess_2014_03.pgn.zst
"""
import argparse
from collections import Counter
from srd.data.lichess import iter_games_text, parse_headers, rating_band, SampleSpec

ap = argparse.ArgumentParser()
ap.add_argument("--file", required=True)
ap.add_argument("--n", type=int, default=20000)
a = ap.parse_args()

spec = SampleSpec()
events, bands, elos = Counter(), Counter(), []
kept = n = 0

for block in iter_games_text(a.file):
    if n >= a.n:
        break
    n += 1
    h = parse_headers(block)
    ev = h.get("Event", "")
    events[ev.split(" http")[0]] += 1
    try:
        w, b = int(h.get("WhiteElo", "0")), int(h.get("BlackElo", "0"))
    except ValueError:
        continue
    if w and b:
        elos.append(min(w, b))
        bands[rating_band(min(w, b))] += 1
    evl = ev.lower()
    if any(tc in evl for tc in spec.time_controls) and block.count(".") >= spec.min_moves:
        kept += 1

print(f"  games inspected      : {n}")
print(f"  pass current filter  : {kept}  ({100*kept/max(n,1):.1f}%)")
if kept == 0:
    print("\n  !! FILTER MATCHES NOTHING. Event names in this file:")
    for e, c in events.most_common(10):
        print(f"       {c:7d}  {e}")
    print("\n  Adjust SampleSpec.time_controls in src/srd/data/lichess.py")
    raise SystemExit(1)

print(f"\n  event types:")
for e, c in events.most_common(8):
    print(f"    {c:7d}  {e}")
print(f"\n  rating bands (by weaker player):")
for b, c in sorted(bands.items()):
    print(f"    {c:7d}  {b}")
empty = [b for b in ("u1400", "1400-1799", "1800-2199", "2200+") if bands.get(b, 0) < 50]
if empty:
    print(f"\n  ! thin/empty bands: {empty} - expect fewer than per_band games there")
if elos:
    import statistics as st
    print(f"\n  Elo (weaker side): median {st.median(elos):.0f}  "
          f"mean {st.mean(elos):.0f}  min {min(elos)}  max {max(elos)}")
