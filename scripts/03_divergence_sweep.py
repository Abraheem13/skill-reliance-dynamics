"""Step 03 - map where measured performance P and true capability S diverge.

This is the paper's central claim. If this sweep comes back empty, the
project's main contribution is falsified and the plan must change.
"""
import json, numpy as np, yaml
from dataclasses import replace
from pathlib import Path
from scipy.integrate import solve_ivp
from srd.model import Params, rhs, observed_performance

cfg = yaml.safe_load(open("config/model_default.yaml"))
base = Params(**{k: cfg[k] for k in
                 ["g", "delta", "kappa", "beta", "c", "lam", "r_cap", "a"]})

rows = []
for kappa in np.linspace(0.4, 1.6, 13):
    for S0 in np.linspace(0.02, 0.60, 30):
        p = replace(base, kappa=float(kappa))
        sol = solve_ivp(rhs, (0, 60), [S0, 0.05], args=(p,),
                        dense_output=True, max_step=0.1, rtol=1e-8, atol=1e-10)
        S, r = sol.sol(60.0)
        P0 = S0 + p.a * 0.05 * (1 - S0)
        rows.append(dict(kappa=float(kappa), S0=float(S0), S=float(S), r=float(r),
                         P=float(observed_performance(S, r, p)),
                         dS=float(S - S0),
                         dP=float(observed_performance(S, r, p) - P0)))

div = [x for x in rows if x["dP"] > 0 and x["dS"] < 0]
print(f"  runs {len(rows)}  divergent {len(div)}  ({100*len(div)/len(rows):.1f}%)")
if div:
    print(f"  divergence above kappa ~ {min(d['kappa'] for d in div):.2f}")
    w = max(div, key=lambda d: d["P"] - d["S"])
    print(f"  worst case: measured P={w['P']:.3f} vs true S={w['S']:.3f}")
else:
    print("  !! NO DIVERGENCE FOUND - central claim not supported at these parameters")

Path("results/fits").mkdir(parents=True, exist_ok=True)
json.dump(rows, open("results/fits/03_divergence_sweep.json", "w"), indent=1)
print("-> results/fits/03_divergence_sweep.json")
