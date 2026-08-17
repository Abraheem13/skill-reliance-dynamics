"""Step 06 - engine-analyse the sample and build the player-year panel.

START SMALL: --limit 200 on the laptop. Sanity-check ACPL (club 40-80cp,
master 15-30cp) before scaling.

    python3 scripts/06_build_panel.py --limit 200 --depth 14
    python3 scripts/06_build_panel.py --depth 16 --threads 8
"""
import argparse, glob, json, time
from pathlib import Path
from srd.data.engine import EngineConfig, open_engine, analyse_game, engine_identity
from srd.data.panel import games_to_long, build_panel, acpl_to_capability

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=None)
ap.add_argument("--depth", type=int, default=16)
ap.add_argument("--threads", type=int, default=1)
ap.add_argument("--engine", default="stockfish")
a = ap.parse_args()

cfg = EngineConfig(path=a.engine, depth=a.depth, threads=a.threads)
ident = engine_identity(cfg)
print(f"  engine: {ident['id'].get('name')}  depth={cfg.depth} threads={cfg.threads}")

files = sorted(glob.glob("data/interim/sample_*.jsonl"))
if not files:
    raise SystemExit("no samples found - run scripts/05 first")

rows, t0, done = [], time.time(), 0
eng = open_engine(cfg)
try:
    for f in files:
        for line in open(f):
            if a.limit and done >= a.limit:
                break
            rec = json.loads(line)
            r = analyse_game(rec["pgn"], eng, cfg)
            if r:
                r["year"] = rec["year"]; r["band"] = rec["band"]
                rows.append(r)
            done += 1
            if done % 25 == 0:
                el = time.time() - t0
                print(f"    {done} games, {el:.0f}s ({el/done:.2f}s/game)")
        if a.limit and done >= a.limit:
            break
finally:
    eng.quit()

Path("data/processed").mkdir(parents=True, exist_ok=True)
long_df = games_to_long(rows)
panel = acpl_to_capability(build_panel(long_df))
long_df.to_csv("data/processed/games_long.csv", index=False)
panel.to_csv("data/processed/panel.csv", index=False)
json.dump(ident, open("data/processed/engine_identity.json", "w"), indent=1)

print(f"\n  games analysed : {len(rows)}")
print(f"  player-games   : {len(long_df)}")
print(f"  panel rows     : {len(panel)}")
if len(panel):
    print(f"  ACPL by year:\n{panel.groupby('year')['acpl'].agg(['mean','count'])}")
print("-> data/processed/panel.csv")
