"""Step 05f - build the longitudinal cohort from monthly dumps only.

No API, no rate limits, fully reproducible from public archives.

  pass 1: scan the LATE dump, keeping games by any 2014 candidate.
          The players found are the survivors.
  pass 2: scan the EARLY dump, keeping games by those same survivors.

Both passes stream; neither holds a dump in memory.
"""
import argparse, json, time
from pathlib import Path
from srd.data.lichess import iter_games_text, parse_headers

ap = argparse.ArgumentParser()
ap.add_argument("--late-dump", required=True)
ap.add_argument("--late", type=int, required=True)
ap.add_argument("--early-dump", required=True)
ap.add_argument("--early", type=int, required=True)
ap.add_argument("--max-per-player", type=int, default=30)
ap.add_argument("--min-moves", type=int, default=20)
a = ap.parse_args()

CAND = "data/interim/candidates.json"
candidates = set(json.load(open(CAND)))
print(f"  candidates from {a.early}: {len(candidates)}", flush=True)

TC = ("classical", "rapid", "blitz")


def scan(dump, year, wanted, out_path):
    counts, kept, seen = {}, 0, 0
    t0 = time.time()
    found = set()
    with open(out_path, "w") as fh:
        for block in iter_games_text(dump):
            seen += 1
            if seen % 2_000_000 == 0:
                el = time.time() - t0
                print(f"    {seen//1_000_000}M games scanned, {kept} kept, "
                      f"{el/60:.0f} min", flush=True)
            h = parse_headers(block)
            ev = h.get("Event", "").lower()
            if not any(t in ev for t in TC):
                continue
            if block.count(".") < a.min_moves:
                continue
            for side in ("White", "Black"):
                u = h.get(side)
                if u in wanted and counts.get(u, 0) < a.max_per_player:
                    counts[u] = counts.get(u, 0) + 1
                    found.add(u)
                    fh.write(json.dumps({"year": year, "band": "cohort",
                                         "player": u, "pgn": block}) + "\n")
                    kept += 1
                    break
    print(f"  {year}: scanned {seen} games, kept {kept} from {len(found)} players "
          f"({(time.time()-t0)/60:.0f} min)", flush=True)
    return found


Path("data/interim").mkdir(parents=True, exist_ok=True)

print(f"\npass 1: {a.late} dump", flush=True)
survivors = scan(a.late_dump, a.late, candidates,
                 f"data/interim/sample_{a.late}.jsonl")
json.dump(sorted(survivors), open("data/interim/cohort.json", "w"), indent=1)
print(f"  survival: {len(survivors)}/{len(candidates)} "
      f"({100*len(survivors)/len(candidates):.1f}%)", flush=True)

print(f"\npass 2: {a.early} dump", flush=True)
early = scan(a.early_dump, a.early, survivors,
             f"data/interim/sample_{a.early}.jsonl")

both = survivors & early
print(f"\n  PLAYERS IN BOTH YEARS: {len(both)}", flush=True)
json.dump(sorted(both), open("data/interim/cohort_both.json", "w"), indent=1)
if len(both) < 30:
    print("  ! thin cohort - widen with more months per year")
