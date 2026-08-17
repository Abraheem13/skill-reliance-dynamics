"""Step 05 - acquire a stratified sample of chess games.

Does NOT download whole monthly dumps. Streams and reservoir-samples.

    python3 scripts/05_download_chess.py --list
    python3 scripts/05_download_chess.py --file data/raw/X.pgn.zst --year 2019
"""
import argparse, json
from pathlib import Path
from srd.data.lichess import month_url, reservoir_sample, SampleSpec

TARGET_MONTHS = [(2014, 3), (2016, 3), (2018, 3), (2020, 3), (2022, 3),
                 (2023, 3), (2024, 3), (2025, 3)]

ap = argparse.ArgumentParser()
ap.add_argument("--list", action="store_true")
ap.add_argument("--file")
ap.add_argument("--year", type=int)
ap.add_argument("--per-band", type=int, default=400)
ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()

if a.list:
    print("Download into data/raw/ (each month is GBs):\n")
    for y, m in TARGET_MONTHS:
        print(f"  curl -L -o data/raw/lichess_{y}_{m:02d}.pgn.zst {month_url(y, m)}")
    print("\nStart with ONE file. Confirm the pipeline before fetching the rest.")
    raise SystemExit

if not a.file or not a.year:
    raise SystemExit("need --file and --year (or --list)")

sample = reservoir_sample(a.file, SampleSpec(per_band=a.per_band, seed=a.seed))
Path("data/interim").mkdir(parents=True, exist_ok=True)
out = f"data/interim/sample_{a.year}.jsonl"
n = 0
with open(out, "w") as fh:
    for band, blocks in sample.items():
        for b in blocks:
            fh.write(json.dumps({"year": a.year, "band": band, "pgn": b}) + "\n")
            n += 1
print(f"  sampled {n} games across {len(sample)} bands -> {out}")
print(f"  per band: { {k: len(v) for k, v in sorted(sample.items())} }")
