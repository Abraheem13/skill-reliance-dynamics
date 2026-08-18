"""Step 10 - pre-submission audit. Every check a reviewer would run."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

print("="*62)
print("AUDIT 1: Bastani effect sizes - adjusted vs unadjusted")
print("="*62)
sd_p, sd_e = 0.287, 0.277
print("  Adjusted (Table 1 regression coefficients / control SD):")
print(f"    Base practice d = {0.137/sd_p:+.4f}   Base exam d = {-0.054/sd_e:+.4f}")
print(f"    divergence = {-0.054/sd_e - 0.137/sd_p:+.4f}")
print("  Unadjusted (Table 8 preregistered t-tests / control SD):")
print(f"    Base practice d = {0.19/sd_p:+.4f}   Base exam d = {-0.035/sd_e:+.4f}")
print(f"    divergence = {-0.035/sd_e - 0.19/sd_p:+.4f}")
print("  -> Both are NEGATIVE. Report the preregistered (unadjusted) as primary,")
print("     adjusted as robustness. State which is which in the paper.")

panel = pd.read_csv("data/processed/panel_within.csv")
long_df = pd.read_csv("data/processed/games_long.csv")

print("\n" + "="*62)
print("AUDIT 2: H3 robustness - does the ACPL decline survive?")
print("="*62)


def h3(p, label):
    w = p.pivot_table(index=["player", "perf"], columns="year", values="acpl")
    if 2014 not in w.columns or 2025 not in w.columns:
        print(f"  {label:<34} n/a"); return None
    w = w[[2014, 2025]].dropna()
    if len(w) < 10:
        print(f"  {label:<34} too few pairs ({len(w)})"); return None
    d = w[2025] - w[2014]
    t, pv = stats.ttest_rel(w[2025], w[2014])
    print(f"  {label:<34} n={len(w):<4} diff={d.mean():+.3f}  p={pv:.4f}")
    return float(d.mean()), float(pv), int(len(w))


base = h3(panel, "PRIMARY (all matched pairs)")

# 2a: exclude the top decile by games played (heavy-player dominance)
tot = panel.groupby("player")["n_games"].sum()
cut = tot.quantile(0.90)
h3(panel[panel.player.isin(tot[tot <= cut].index)], "excl. top-decile game count")

# 2b: blitz only (the dominant time control)
h3(panel[panel.perf == "blitz"], "blitz only")

# 2c: require more games per player-year
h3(panel[panel.n_games >= 12], "n_games >= 12")

# 2d: require more positions
h3(panel[panel.n_positions >= 300], "n_positions >= 300")

# 2e: trimmed - drop extreme ACPL
lo, hi = panel.acpl.quantile([0.02, 0.98])
h3(panel[panel.acpl.between(lo, hi)], "ACPL 2-98 percentile trimmed")

print("\n" + "="*62)
print("AUDIT 3: S mapping bounds - is the result an artefact of lo/hi?")
print("="*62)
for lo_, hi_ in [(5,150), (10,120), (15,100), (0,200)]:
    p2 = panel.copy()
    p2["S"] = 1.0 - (p2["acpl"].clip(lo_, hi_) - lo_) / (hi_ - lo_)
    w = p2.pivot_table(index=["player","perf"], columns="year", values="S")
    if 2014 in w.columns and 2025 in w.columns:
        w = w[[2014,2025]].dropna()
        d = w[2025] - w[2014]
        t, pv = stats.ttest_rel(w[2025], w[2014])
        print(f"  lo={lo_:<4} hi={hi_:<4} mean dS={d.mean():+.4f}  p={pv:.4f}")
print("  -> sign and significance must be stable across all rows")

print("\n" + "="*62)
print("AUDIT 4: heavy-player concentration")
print("="*62)
g = long_df.groupby("player")["n_positions"].sum().sort_values(ascending=False)
print(f"  players: {len(g)}   total positions: {g.sum():,}")
print(f"  top 1%  hold {100*g.head(max(1,len(g)//100)).sum()/g.sum():.1f}% of positions")
print(f"  top 10% hold {100*g.head(max(1,len(g)//10)).sum()/g.sum():.1f}% of positions")
print("  -> if top 10% exceed ~35%, report the excl-top-decile result too")

print("\n" + "="*62)
print("AUDIT 5: per-year sample balance")
print("="*62)
print(panel.groupby("year").agg(
    players=("player","nunique"), rows=("player","size"),
    mean_games=("n_games","mean"), mean_pos=("n_positions","mean")).round(1))
print("\n  time control mix by year:")
print(pd.crosstab(panel.year, panel.perf))

print("\n" + "="*62)
print("AUDIT 6: declared limitations (cannot be tested - must be stated)")
print("="*62)
for s in ["Age/development: players aged 11 years; improvement may be developmental,",
          "  so 'no decline' may mean 'decline masked'. State as a power limitation.",
          "Survivorship: cohort = accounts active in BOTH 2014 and 2025.",
          "Engine depth 12 (not 16+): adequate for group means, note as limitation.",
          "Reliance r is NOT observed in chess; inferred from r_cap structure only.",
          "H4 is k=1 study: a demonstration, not a meta-analysis."]:
    print("  " + s)

Path("results/fits").mkdir(parents=True, exist_ok=True)
json.dump({"primary_h3": base}, open("results/fits/11_audit.json","w"), indent=1)
print("\n-> results/fits/11_audit.json")
