"""Step 01 - locate equilibria and classify their stability."""
import json, yaml
from pathlib import Path
from srd.model import Params
from srd.model.equilibria import equilibria, classify

cfg = yaml.safe_load(open("config/model_default.yaml"))
p = Params(**{k: cfg[k] for k in
              ["g", "delta", "kappa", "beta", "c", "lam", "r_cap", "a"]})

E = equilibria(p)
out = []
for S in E:
    kind, ev = classify(S, p)
    out.append(dict(S=round(float(S), 6), kind=kind,
                    eigenvalues=[complex(x).real for x in ev]))
    print(f"  S* = {S:8.4f}   {kind:<9} eigenvalues = {[round(complex(x).real,4) for x in ev]}")

Path("results/fits").mkdir(parents=True, exist_ok=True)
json.dump(dict(params=p.to_dict(), equilibria=out),
          open("results/fits/01_equilibria.json", "w"), indent=1)
print("\n-> results/fits/01_equilibria.json")
