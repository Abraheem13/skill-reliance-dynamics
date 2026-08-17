"""Step 04 - numerically verify each analytic proposition."""
import json, yaml, numpy as np
from dataclasses import replace
from pathlib import Path
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from srd.model import Params, rhs, reduced_rhs, observed_performance
from srd.model.equilibria import equilibria, classify
from srd.model.bifurcation import kappa_star, is_bistable
from srd.model import analysis as A

cfg = yaml.safe_load(open("config/model_default.yaml"))
p = Params(**{k: cfg[k] for k in
              ["g", "delta", "kappa", "beta", "c", "lam", "r_cap", "a"]})
report = {}

print("P1  forward invariance of [0,1]^2")
bf = A.boundary_flow(p)
ok1 = (bf["S=0"][0] >= -1e-12 and bf["S=1"][1] <= 1e-12
       and bf["r=0"][0] >= -1e-12 and bf["r=1"][1] <= 1e-12)
for e, (lo, hi) in bf.items():
    print(f"      edge {e}: normal flow in [{lo:+.4f}, {hi:+.4f}]")
print(f"      => {'HOLDS' if ok1 else 'FAILS'}")
report["P1_invariance"] = bool(ok1)

print("\nP2  no-AI baseline is unique and equals g/(g+delta)")
p0 = replace(p, r_cap=0.0)
E0 = equilibria(p0)
pred = A.baseline_equilibrium(p0)
ok2 = len(E0) == 1 and abs(E0[0] - pred) < 1e-9
print(f"      predicted {pred:.6f}   found {E0}   => {'HOLDS' if ok2 else 'FAILS'}")
report["P2_baseline"] = bool(ok2)

print("\nP3  necessary condition: beta*c*r_cap > 4*delta/g")
viol = 0
rng = np.random.default_rng(0)
for _ in range(4000):
    q = Params(g=rng.uniform(0.05, 1.0), delta=rng.uniform(0.01, 0.5),
               kappa=rng.uniform(-1, 2), beta=rng.uniform(1, 15),
               c=rng.uniform(0.2, 4), lam=1.5,
               r_cap=rng.uniform(0.0, 1.0), a=0.9)
    if is_bistable(q) and not A.necessary_condition_holds(q):
        viol += 1
print(f"      loop gain {A.loop_gain(p):.2f}  vs bound {A.bistability_bound(p):.2f}")
print(f"      counterexamples in 4000 random draws: {viol}  => "
      f"{'HOLDS' if viol == 0 else 'FAILS'}")
report["P3_necessary_condition"] = bool(viol == 0)
report["P3_counterexamples"] = int(viol)

print("\nP4  the fold is a genuine saddle-node (transversality)")
ks = kappa_star(p, -1.0, 2.0, 121)
pk = replace(p, kappa=ks)
Sg = np.linspace(1e-4, 0.999, 20001)
fp = np.array([A.F_prime(s, pk) for s in Sg])
idx = np.where(np.sign(fp[:-1]) != np.sign(fp[1:]))[0]
Sfold = None
for i in idx:
    s = brentq(A.F_prime, Sg[i], Sg[i + 1], args=(pk,))
    if abs(reduced_rhs(s, pk)) < 1e-3:
        Sfold = s
        break
if Sfold is not None:
    tr = A.transversality(Sfold, pk)
    ok4 = abs(tr) > 1e-9
    print(f"      kappa* = {ks:.6f}   fold at S = {Sfold:.6f}")
    print(f"      residual |F|,|F'| = {np.abs(A.fold_residual(Sfold, pk))}")
    print(f"      dF/dkappa = {tr:.6f}  => {'HOLDS' if ok4 else 'FAILS'}")
else:
    ok4 = False
    print("      fold point not located => FAILS")
report["P4_saddle_node"] = bool(ok4)
report["kappa_star"] = float(ks)

print("\nP5  divergence condition matches simulated trajectories")
q = replace(p, kappa=0.9)
sol = solve_ivp(rhs, (0, 60), [0.10, 0.05], args=(q,), dense_output=True,
                max_step=0.05, rtol=1e-9, atol=1e-11)
t = np.linspace(0.01, 60, 4000)
S, r = sol.sol(t)
agree = 0
for i in range(len(t)):
    _, _, holds = A.divergence_condition(S[i], r[i], q)
    dP = A.dP_dt(S[i], r[i], q)
    dS = q.g * (1 - r[i]) * (1 - S[i]) - q.delta * S[i]
    if holds == (dP > 0 and dS < 0):
        agree += 1
ok5 = agree == len(t)
frac = np.mean([A.divergence_condition(S[i], r[i], q)[2] for i in range(len(t))])
print(f"      condition agrees with simulation at {agree}/{len(t)} points")
print(f"      trajectory spends {100*frac:.1f}% of time in the divergent regime")
print(f"      => {'HOLDS' if ok5 else 'FAILS'}")
report["P5_divergence"] = bool(ok5)

print("\n" + "=" * 46)
allok = all(report[k] for k in
            ["P1_invariance", "P2_baseline", "P3_necessary_condition",
             "P4_saddle_node", "P5_divergence"])
print("ALL PROPOSITIONS VERIFIED" if allok else "SOME PROPOSITIONS FAILED")
Path("results/fits").mkdir(parents=True, exist_ok=True)
json.dump(report, open("results/fits/04_propositions.json", "w"), indent=1)
print("-> results/fits/04_propositions.json")
