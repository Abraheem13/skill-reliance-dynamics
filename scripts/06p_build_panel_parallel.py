"""Step 06p - engine-analyse in parallel, one Stockfish per worker.

Stockfish's internal threading scales badly for short fixed-depth analyses, so
we run N independent single-threaded engines instead and split games across
them. This is what actually uses a many-core machine.

    python3 scripts/06p_build_panel_parallel.py --workers 32 --depth 16
"""
import argparse, glob, json, time
from pathlib import Path
from multiprocessing import Pool, current_process
from srd.data.engine import EngineConfig, open_engine, analyse_game, engine_identity
from srd.data.panel import games_to_long, build_panel, acpl_to_capability, within_player

ap = argparse.ArgumentParser()
ap.add_argument("--workers", type=int, default=4)
ap.add_argument("--depth", type=int, default=16)
ap.add_argument("--engine", default="stockfish")
ap.add_argument("--limit", type=int, default=None)
a = ap.parse_args()

CFG = EngineConfig(path=a.engine, depth=a.depth, threads=1, hash_mb=128)
_engine = {}


def _init():
    _engine["e"] = open_engine(CFG)


def _work(rec):
    try:
        r = analyse_game(rec["pgn"], _engine["e"], CFG)
    except Exception:
        return None
    if not r:
        return None
    r["year"] = rec["year"]
    r["band"] = rec.get("band", "cohort")
    return r


if __name__ == "__main__":
    recs = []
    for f in sorted(glob.glob("data/interim/sample_*.jsonl")):
        for line in open(f):
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    if a.limit:
        recs = recs[:a.limit]
    print(f"  games to analyse : {len(recs)}")
    print(f"  workers          : {a.workers}   depth: {a.depth}")

    t0 = time.time()
    rows = []
    with Pool(a.workers, initializer=_init) as pool:
        for i, r in enumerate(pool.imap_unordered(_work, recs, chunksize=8), 1):
            if r:
                rows.append(r)
            if i % 500 == 0:
                el = time.time() - t0
                rate = i / el
                print(f"    {i}/{len(recs)}  {el/60:.1f} min  "
                      f"{rate:.1f} games/s  eta {(len(recs)-i)/rate/60:.0f} min",
                      flush=True)

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    long_df = games_to_long(rows)
    panel = acpl_to_capability(build_panel(long_df))
    primary = within_player(panel)

    long_df.to_csv("data/processed/games_long.csv", index=False)
    panel.to_csv("data/processed/panel.csv", index=False)
    primary.to_csv("data/processed/panel_within.csv", index=False)
    json.dump(engine_identity(CFG), open("data/processed/engine_identity.json", "w"), indent=1)

    print(f"\n  analysed      : {len(rows)} games in {(time.time()-t0)/60:.1f} min")
    print(f"  panel rows    : {len(panel)}")
    print(f"  WITHIN-PLAYER : {len(primary)} rows, "
          f"{primary.player.nunique() if len(primary) else 0} players")
    if len(primary):
        print("\n", primary.groupby(['year'])[['acpl','S']].agg(['mean','count']))
    print("\n-> data/processed/panel_within.csv")
