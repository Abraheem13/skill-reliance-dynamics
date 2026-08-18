"""Step 09 - fit the model to MULTI-YEAR trajectories.

With 3+ time points per player, lambda is identified from the trajectory shape
rather than inferred from cross-sectional mean reversion. This also lets us
TEST the model's functional form instead of assuming it.

Per player:  S(t) = S_eq + (S0 - S_eq) exp(-lam (t - t0))

Shared lam and S_eq across players, individual S0. Compared against a linear
null to see whether the exponential form earns its extra parameter.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import least_squares

R_CHESS = 0.05
panel = pd.read_csv("data/processed/panel_within.csv")
years = sorted(panel.year.unique())
print(f"  years in panel: {years}")

cnt = panel.groupby(["player", "perf"])["year"].nunique()
keep = set(cnt[cnt >= 3].index)
p = panel[[(a, b) in keep for a, b in zip(panel.player, panel.perf)]]
print(f"  players with 3+ years: {p.player.nunique()}   rows: {len(p)}")
if p.player.nunique() < 20:
    raise SystemExit("  too few multi-year players")

t0 = min(years)
groups = [(d.year.values - t0, d.S.values) for _, d in p.groupby(["player", "perf"])]
n_g = len(groups)


def resid(th):
    lam, S_eq, S0s = th[0], th[1], th[2:]
    return np.concatenate([S - (S_eq + (S0s[k] - S_eq) * np.exp(-lam * t))
                           for k, (t, S) in enumerate(groups)])


init = np.concatenate([[0.05, 0.65], [S[0] for _, S in groups]])
lo = np.concatenate([[1e-4, 0.01], np.zeros(n_g)])
hi = np.concatenate([[2.0, 0.99], np.ones(n_g)])
fit = least_squares(resid, init, bounds=(lo, hi), max_nfev=30000)
lam, S_eq = fit.x[0], fit.x[1]
rss_exp = float((fit.fun ** 2).sum())


def resid_lin(th):
    b, a0 = th[0], th[1:]
    return np.concatenate([S - (a0[k] + b * t) for k, (t, S) in enumerate(groups)])


fit_l = least_squares(resid_lin,
                      np.concatenate([[0.001], [S[0] for _, S in groups]]),
                      max_nfev=30000)
rss_lin = float((fit_l.fun ** 2).sum())

n_obs = len(fit.fun)
aic_exp = n_obs * np.log(rss_exp / n_obs) + 2 * (n_g + 2)
aic_lin = n_obs * np.log(rss_lin / n_obs) + 2 * (n_g + 1)

print(f"\n  lambda (rate)   : {lam:.4f} /yr")
print(f"  S_eq            : {S_eq:.4f}")
print(f"  decay over span : {np.exp(-lam*(max(years)-t0)):.4f}")
print(f"\n  exponential RSS : {rss_exp:.4f}  AIC {aic_exp:.1f}")
print(f"  linear RSS      : {rss_lin:.4f}  AIC {aic_lin:.1f}")
print(f"  -> {'EXPONENTIAL preferred' if aic_exp < aic_lin else 'LINEAR preferred (model form NOT supported)'}")

g_hat = S_eq * lam / (1 - R_CHESS)
d_hat = (1 - S_eq) * lam
print(f"\n  g       : {g_hat:.4f}")
print(f"  delta   : {d_hat:.4f}")
print(f"  delta/g : {d_hat/g_hat:.4f}")

rng = np.random.default_rng(0)
boot = []
for _ in range(200):
    idx = rng.integers(0, n_g, n_g)
    sub = [groups[i] for i in idx]
    def rs(th, sub=sub):
        l_, s_, S0s = th[0], th[1], th[2:]
        return np.concatenate([S - (s_ + (S0s[k]-s_)*np.exp(-l_*t))
                               for k, (t, S) in enumerate(sub)])
    try:
        f = least_squares(rs,
                          np.concatenate([[lam, S_eq], [S[0] for _, S in sub]]),
                          bounds=(np.concatenate([[1e-4,0.01], np.zeros(len(sub))]),
                                  np.concatenate([[2.0,0.99], np.ones(len(sub))])),
                          max_nfev=4000)
        boot.append((f.x[0], f.x[1]))
    except Exception:
        pass
boot = np.array(boot)
out = dict(years=[int(y) for y in years], n_players=int(p.player.nunique()),
           lam=float(lam), S_eq=float(S_eq), g=float(g_hat), delta=float(d_hat),
           delta_over_g=float(d_hat/g_hat), rss_exp=rss_exp, rss_lin=rss_lin,
           aic_exp=float(aic_exp), aic_lin=float(aic_lin),
           exponential_preferred=bool(aic_exp < aic_lin))
if len(boot) > 20:
    print()
    for k, nm in enumerate(["lambda", "S_eq"]):
        lo_, hi_ = np.percentile(boot[:, k], [2.5, 97.5])
        print(f"  {nm:<7} 95% CI [{lo_:.4f}, {hi_:.4f}]")
    out["ci"] = {nm: [float(np.percentile(boot[:,k],2.5)),
                      float(np.percentile(boot[:,k],97.5))]
                 for k, nm in enumerate(["lambda","S_eq"])}

Path("results/fits").mkdir(parents=True, exist_ok=True)
json.dump(out, open("results/fits/10_multiyear.json", "w"), indent=1)
print("\n-> results/fits/10_multiyear.json")
