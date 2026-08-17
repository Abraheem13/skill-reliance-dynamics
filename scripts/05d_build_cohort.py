"""Step 05d - build the longitudinal player cohort.

Replaces game-centric sampling for the primary analysis. Produces accounts
observed in BOTH an early and a late year.

    python3 scripts/05d_build_cohort.py --harvest data/raw/lichess_2014_03.pgn.zst
    python3 scripts/05d_build_cohort.py --screen --late 2025 --limit 300
    python3 scripts/05d_build_cohort.py --fetch --early 2014 --late 2025
"""
import argparse, json, time
from pathlib import Path
from srd.data.lichess_api import harvest_usernames, is_active_in, fetch_user_games

ap = argparse.ArgumentParser()
ap.add_argument("--harvest")
ap.add_argument("--screen", action="store_true")
ap.add_argument("--fetch", action="store_true")
ap.add_argument("--early", type=int, default=2014)
ap.add_argument("--late", type=int, default=2025)
ap.add_argument("--limit", type=int, default=300)
ap.add_argument("--max-games", type=int, default=40)
ap.add_argument("--sleep", type=float, default=1.0)
ap.add_argument("--only-year", type=int, default=None)
a = ap.parse_args()

Path("data/interim").mkdir(parents=True, exist_ok=True)
CAND = "data/interim/candidates.json"
COHORT = "data/interim/cohort.json"

if a.harvest:
    users = harvest_usernames(a.harvest, limit=4000)
    json.dump(users, open(CAND, "w"), indent=1)
    print(f"  harvested {len(users)} candidate usernames -> {CAND}")
    raise SystemExit

if a.screen:
    users = json.load(open(CAND))
    survivors, checked = [], 0
    for u in users:
        if len(survivors) >= a.limit:
            break
        checked += 1
        try:
            if is_active_in(u, a.late):
                survivors.append(u)
        except Exception as e:
            print(f"    skip {u}: {e}")
        time.sleep(a.sleep)
        if checked % 25 == 0:
            print(f"    checked {checked}, survivors {len(survivors)} "
                  f"({100*len(survivors)/checked:.0f}%)")
    json.dump(survivors, open(COHORT, "w"), indent=1)
    print(f"\n  cohort: {len(survivors)} accounts active in {a.late} "
          f"out of {checked} checked ({100*len(survivors)/max(checked,1):.0f}% survival)")
    print(f"-> {COHORT}")
    print("\n  NOTE: survivorship bias is real. Report this rate in the paper.")
    raise SystemExit

if a.fetch:
    cohort = json.load(open(COHORT))
    years = (a.only_year,) if a.only_year else (a.early, a.late)
    for year in years:
        out = f"data/interim/sample_{year}.jsonl"
        n, users_with_games = 0, 0
        with open(out, "w") as fh:
            for i, u in enumerate(cohort):
                got = 0
                try:
                    for block in fetch_user_games(u, year, max_games=a.max_games):
                        fh.write(json.dumps({"year": year, "band": "cohort",
                                             "player": u, "pgn": block}) + "\n")
                        n += 1; got += 1
                except Exception as e:
                    print(f"    {u} {year}: {e}")
                if got:
                    users_with_games += 1
                time.sleep(a.sleep)
                if (i + 1) % 25 == 0:
                    print(f"    {year}: {i+1}/{len(cohort)} users, {n} games")
        print(f"  {year}: {n} games from {users_with_games} users -> {out}")
    raise SystemExit

ap.print_help()
