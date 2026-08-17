"""Step 05c - find players appearing in MULTIPLE years.

The Lichess pool composition changed enormously across the engine era, so
comparing mean ACPL across years mostly measures who joined, not whether
humans changed. The within-player design strips composition out: only accounts
observed in two or more years enter the primary analysis.

Chess analogue of the within-family design in Bratsberg & Rogeberg (2018, PNAS).

    python3 scripts/05c_repeat_players.py
"""
import glob, json
from collections import defaultdict
from pathlib import Path
from srd.data.lichess import parse_headers

seen = defaultdict(set)
files = sorted(glob.glob("data/interim/sample_*.jsonl"))
if not files:
    raise SystemExit("no samples found - run scripts/05 first")

for f in files:
    for line in open(f):
        rec = json.loads(line)
        h = parse_headers(rec["pgn"])
        for side in ("White", "Black"):
            p = h.get(side)
            if p:
                seen[p].add(rec["year"])

repeat = {p: sorted(y) for p, y in seen.items() if len(y) >= 2}
print(f"  distinct players    : {len(seen)}")
print(f"  in 2+ years         : {len(repeat)}  ({100*len(repeat)/max(len(seen),1):.1f}%)")
if repeat:
    span = [max(y) - min(y) for y in repeat.values()]
    print(f"  median year span    : {sorted(span)[len(span)//2]}")

Path("data/interim").mkdir(parents=True, exist_ok=True)
json.dump(repeat, open("data/interim/repeat_players.json", "w"), indent=1)
print("-> data/interim/repeat_players.json")

if len(repeat) < 100:
    print("\n  ! FEW REPEAT PLAYERS. The within-player design needs more.")
    print("    Options: raise --per-band, sample adjacent months, or accept")
    print("    the between-player design and declare composition as a")
    print("    limitation in the paper. Do NOT silently switch designs.")
