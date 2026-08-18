"""Step 05g - add one more year to the existing cohort.

Scans a dump for games by players ALREADY in cohort_both.json, so the panel
stays the same people across all years. Single-threaded: cores do not help
here, only the engine step benefits.
"""
import argparse, json, time
from pathlib import Path
from srd.data.lichess import iter_games_text, parse_headers

ap = argparse.ArgumentParser()
ap.add_argument("--dump", required=True)
ap.add_argument("--year", type=int, required=True)
ap.add_argument("--players", default="data/interim/cohort_both.json")
ap.add_argument("--max-per-player", type=int, default=30)
ap.add_argument("--min-moves", type=int, default=20)
a = ap.parse_args()

wanted = set(json.load(open(a.players)))
print(f"  tracking {len(wanted)} cohort players", flush=True)
TC = ("classical", "rapid", "blitz")

counts, kept, seen, found = {}, 0, 0, set()
t0 = time.time()
out = f"data/interim/sample_{a.year}.jsonl"
Path("data/interim").mkdir(parents=True, exist_ok=True)
with open(out, "w") as fh:
    for block in iter_games_text(a.dump):
        seen += 1
        if seen % 2_000_000 == 0:
            print(f"    {seen//1_000_000}M scanned, {kept} kept, "
                  f"{(time.time()-t0)/60:.0f} min", flush=True)
        h = parse_headers(block)
        if not any(t in h.get("Event", "").lower() for t in TC):
            continue
        if block.count(".") < a.min_moves:
            continue
        for side in ("White", "Black"):
            u = h.get(side)
            if u in wanted and counts.get(u, 0) < a.max_per_player:
                counts[u] = counts.get(u, 0) + 1
                found.add(u)
                fh.write(json.dumps({"year": a.year, "band": "cohort",
                                     "player": u, "pgn": block}) + "\n")
                kept += 1
                break

print(f"\n  {a.year}: {kept} games from {len(found)}/{len(wanted)} cohort players "
      f"({(time.time()-t0)/60:.0f} min)")
print(f"  coverage: {100*len(found)/len(wanted):.1f}%")
print(f"-> {out}")
