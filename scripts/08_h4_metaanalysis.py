"""Step 08 - H4: do AI-REMOVED outcomes show smaller effects than AI-PRESENT?"""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ap = argparse.ArgumentParser()
ap.add_argument("--file", default="data/h4/coded_studies.csv")
a = ap.parse_args()

d = pd.read_csv(a.file)
d = d[~d.study_id.astype(str).str.startswith("EXAMPLE")]
if d.empty:
    raise SystemExit("no coded studies yet - fill data/h4/coded_studies.csv")

m = d.se.isna() & d.ci_low.notna() & d.ci_high.notna()
d.loc[m, "se"] = (d.loc[m, "ci_high"] - d.loc[m, "ci_low"]) / 3.92
m = d.se.isna() & d.n_treatment.notna() & d.n_control.notna()
d.loc[m, "se"] = np.sqrt(1/d.loc[m,"n_treatment"] + 1/d.loc[m,"n_control"]
                         + d.loc[m,"effect_size"]**2
                         / (2*(d.loc[m,"n_treatment"]+d.loc[m,"n_control"])))
d = d.dropna(subset=["effect_size","se"])
d = d[d.ai_condition.isin(["AI_PRESENT","AI_REMOVED"])]


def re_meta(y, se):
    w = 1/se**2
    fe = (w*y).sum()/w.sum()
    Q = (w*(y-fe)**2).sum(); df = len(y)-1
    C = w.sum() - (w**2).sum()/w.sum()
    tau2 = max(0.0, (Q-df)/C) if C > 0 else 0.0
    wr = 1/(se**2+tau2)
    return (wr*y).sum()/wr.sum(), np.sqrt(1/wr.sum()), tau2, \
           (max(0.0,(Q-df)/Q)*100 if Q > 0 else 0.0)


res = {}
print(f"  effect sizes: {len(d)}   studies: {d.study_id.nunique()}\n")
for cond in ("AI_PRESENT","AI_REMOVED"):
    s = d[d.ai_condition == cond]
    if len(s) < 2:
        print(f"  {cond}: only {len(s)} effect size(s) - cannot pool"); continue
    p_, sp, tau2, I2 = re_meta(s.effect_size.values, s.se.values)
    lo, hi = p_-1.96*sp, p_+1.96*sp
    print(f"  {cond:<11} k={len(s):<3} d={p_:+.3f} [{lo:+.3f}, {hi:+.3f}]  I2={I2:.0f}%")
    res[cond] = dict(k=int(len(s)), d=float(p_), se=float(sp),
                     ci=[float(lo),float(hi)], I2=float(I2), tau2=float(tau2))

if "AI_PRESENT" in res and "AI_REMOVED" in res:
    diff = res["AI_REMOVED"]["d"] - res["AI_PRESENT"]["d"]
    se_d = np.sqrt(res["AI_REMOVED"]["se"]**2 + res["AI_PRESENT"]["se"]**2)
    z = diff/se_d; pv = 2*(1-stats.norm.cdf(abs(z)))
    print(f"\n  DIFFERENCE (REMOVED - PRESENT): {diff:+.3f} "
          f"[{diff-1.96*se_d:+.3f}, {diff+1.96*se_d:+.3f}]  z={z:.2f}  p={pv:.4f}")
    print(f"  H4 predicts NEGATIVE -> "
          f"{'SUPPORTED' if diff < 0 and pv < 0.05 else 'NOT SUPPORTED'}")
    res["difference"] = dict(diff=float(diff), se=float(se_d), z=float(z),
                             p=float(pv), supported=bool(diff<0 and pv<0.05))

both = d.groupby("study_id").ai_condition.nunique()
pids = both[both == 2].index
if len(pids) >= 2:
    rows = np.array([d[(d.study_id==s)&(d.ai_condition=="AI_REMOVED")].effect_size.mean()
                     - d[(d.study_id==s)&(d.ai_condition=="AI_PRESENT")].effect_size.mean()
                     for s in pids])
    t, pv = stats.ttest_1samp(rows, 0)
    print(f"\n  WITHIN-STUDY contrasts: k={len(rows)}  mean diff={rows.mean():+.3f}  "
          f"t={t:.2f}  p={pv:.4f}")
    print("  (no between-study confounding - cleanest test)")
    res["within_study"] = dict(k=int(len(rows)), mean_diff=float(rows.mean()),
                               t=float(t), p=float(pv))
else:
    print(f"\n  within-study contrasts: only {len(pids)} study reports both")

for cond in ("AI_PRESENT","AI_REMOVED"):
    s = d[d.ai_condition == cond]
    if len(s) >= 10:
        sl, ic, r, pv, _ = stats.linregress(1/s.se, s.effect_size/s.se)
        print(f"  Egger {cond}: intercept={ic:.3f} p={pv:.4f}"
              f"{'  <- asymmetry' if pv < 0.10 else ''}")
        res.setdefault("egger",{})[cond] = dict(intercept=float(ic), p=float(pv))

Path("results/fits").mkdir(parents=True, exist_ok=True)
json.dump(res, open("results/fits/09_h4.json","w"), indent=1)
print("\n-> results/fits/09_h4.json")
