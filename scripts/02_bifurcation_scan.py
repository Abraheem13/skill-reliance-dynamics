"""Step 02 - find the tipping point kappa* in AI capability."""
import json, yaml
from pathlib import Path
from srd.model import Params
from srd.model.bifurcation import kappa_star, scan_kappa

cfg = yaml.safe_load(open("config/model_default.yaml"))
p = Params(**{k: cfg[k] for k in
              ["g", "delta", "kappa", "beta", "c", "lam", "r_cap", "a"]})

ks, eqs, ns = scan_kappa(p, -1.0, 2.0, 121)
kstar = kappa_star(p, -1.0, 2.0, 121)
print(f"  max stable equilibria : {int(ns.max())}")
print(f"  bistability onset     : kappa* = {kstar}")

Path("results/fits").mkdir(parents=True, exist_ok=True)
json.dump(dict(kappa_star=kstar,
               kappa=[float(k) for k in ks],
               n_stable=[int(n) for n in ns]),
          open("results/fits/02_bifurcation.json", "w"), indent=1)
print("-> results/fits/02_bifurcation.json")
