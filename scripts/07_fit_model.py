"""Step 07 - fit the model's learning/forgetting parameters to the chess panel.

Method
------
Under low r_cap (engines banned in play) the reduced model has a closed form:

    S(t) = S_eq + (S0 - S_eq) exp(-lam t),   lam = g(1-r) + delta
    S_eq = g(1-r) / lam

With two time points and cross-sectional spread in S0, lam is identified from
MEAN REVERSION: regressing S1 on S0 gives slope = exp(-lam t).

Critical correction: measurement error in S0 attenuates that slope and biases
lam upward (classic regression-to-the-mean). We estimate each player-year's
measurement variance from game-level ACPL scatter and correct for it.

Identifiability is checked and reported, not assumed. If exp(-lam*t) < 0.1 the
system has fully equilibrated within the observation gap and the RATE leaves no
trace in the data - only S_eq is then identifiable, and the script says so.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

GAP = 11.0          # 2014 -> 2025
ACPL_LO, ACPL_HI = 10.0, 120.0     # fixed S scaling, must match panel.py
R_CHESS = 0.05      # assumed reliance during rated play (engines banned)

long_df = pd.read_csv("data/processed/games_long.csv")
panel = pd.read_csv("data/processed/panel_within.csv")

# --- measurement error per player-year, from game-level scatter -------------
g = long_df.groupby(["player", "year"])["acpl"]
se = (g.std() / np.sqrt(g.count())).rename("acpl_se").reset_index()
se["S_se"] = se["acpl_se"] / (ACPL_HI - ACPL_LO)
panel = panel.merge(se[["player", "year", "S_se"]], on=["player", "year"], how="left")

w = panel.pivot_table(index=["player", "perf"], columns="year",
                      values=["S", "S_se"]).dropna()
S0, S1 = w[("S", 2014)].values, w[("S", 2025)].values
E0, E1 = w[("S_se", 2014)].values, w[("S_se", 2025)].values
n = len(S0)
print(f"  matched pairs        : {n}")
print(f"  mean S 2014 / 2025   : {S0.mean():.4f} / {S1.mean():.4f}")
print(f"  mean measurement SE  : {E0.mean():.4f} / {E1.mean():.4f}")


def fit(S0, S1, E0):
    b, _ = np.polyfit(S0, S1, 1)
    var_obs = S0.var(ddof=1)
    var_err = np.mean(E0 ** 2)
    rel = max((var_obs - var_err) / var_obs, 1e-6)      # reliability
    b_corr = float(np.clip(b / rel, 1e-9, 0.999999))
    lam = -np.log(b_corr) / GAP
    a_corr = S1.mean() - b_corr * S0.mean()
    S_eq = a_corr / (1 - b_corr) if abs(1 - b_corr) > 1e-9 else np.nan
    return b, b_corr, rel, lam, S_eq


b, b_corr, rel, lam, S_eq = fit(S0, S1, E0)
print(f"\n  naive slope          : {b:.4f}")
print(f"  reliability          : {rel:.4f}")
print(f"  corrected slope      : {b_corr:.4f}")
print(f"  lambda (rate)        : {lam:.4f} /yr")
print(f"  S_eq (equilibrium)   : {S_eq:.4f}")

# --- identifiability check --------------------------------------------------
decay = np.exp(-lam * GAP)
identifiable = 0.10 < decay < 0.90
print(f"\n  exp(-lam*t)          : {decay:.4f}")
print(f"  rate identifiable    : {'YES' if identifiable else 'NO - system has'}"
      f"{'' if identifiable else ' equilibrated; only S_eq is identified'}")

# --- recover g and delta ----------------------------------------------------
g_hat = S_eq * lam / (1 - R_CHESS)
d_hat = (1 - S_eq) * lam
print(f"\n  g     (learning)     : {g_hat:.4f}   (assuming r={R_CHESS})")
print(f"  delta (forgetting)   : {d_hat:.4f}")
print(f"  delta/g ratio        : {d_hat/g_hat:.4f}   <- identified even if rate is not")

# --- bootstrap --------------------------------------------------------------
rng = np.random.default_rng(0)
B = 2000
boot = []
for _ in range(B):
    i = rng.integers(0, n, n)
    try:
        _, _, _, l_, s_ = fit(S0[i], S1[i], E0[i])
        if np.isfinite(l_) and np.isfinite(s_) and 0 < s_ < 1:
            boot.append((l_, s_, s_*l_/(1-R_CHESS), (1-s_)*l_))
    except Exception:
        pass
boot = np.array(boot)
names = ["lambda", "S_eq", "g", "delta"]
print(f"\n  bootstrap ({len(boot)} resamples):")
for k, nm in enumerate(names):
    lo, hi = np.percentile(boot[:, k], [2.5, 97.5])
    print(f"    {nm:<7} {boot[:,k].mean():.4f}  95% CI [{lo:.4f}, {hi:.4f}]")

out = dict(n_pairs=int(n), gap_years=GAP, r_assumed=R_CHESS,
           slope_naive=float(b), reliability=float(rel),
           slope_corrected=float(b_corr), lam=float(lam), S_eq=float(S_eq),
           g=float(g_hat), delta=float(d_hat), delta_over_g=float(d_hat/g_hat),
           decay_over_gap=float(decay), rate_identifiable=bool(identifiable),
           ci={nm: [float(np.percentile(boot[:, k], 2.5)),
                    float(np.percentile(boot[:, k], 97.5))]
               for k, nm in enumerate(names)})
Path("results/fits").mkdir(parents=True, exist_ok=True)
json.dump(out, open("results/fits/08_chess_params.json", "w"), indent=1)
print("\n-> results/fits/08_chess_params.json")
