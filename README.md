# Skill–Reliance Dynamics (SRD)

Formal model of cognitive offloading to AI, with the central claim that
**measured performance and retained capability can move in opposite directions.**

## The idea in one paragraph

Nearly every published effect size on generative AI in education measures a
learner's score *with AI available*. The model here separates that observed
performance `P` from unassisted capability `S` — what the learner can do when
the AI is taken away. Under a wide range of parameters the model predicts
`P` rising while `S` falls. If true, the positive meta-analytic literature
(SMD ≈ 0.45) and the widespread concern about children's skills are not in
conflict: they are measuring different variables.

## Model

```
dS/dt = g (1 - r)(1 - S) - delta * S
dr/dt = lam [ r_cap * sigmoid(beta (kappa - c S)) - r ]
P     = S + a * r * (1 - S)
```

| symbol | meaning |
|---|---|
| `S` | unassisted capability, [0,1] |
| `r` | fraction of cognitive work offloaded, [0,1] |
| `P` | observed/assisted performance — what studies measure |
| `g` | practice gain rate (task frequency, instruction quality) |
| `delta` | forgetting rate |
| `kappa` | AI capability relative to learner |
| `beta` | steepness of reliance response (habit formation) |
| `c` | suppression of reliance by own capability (self-confidence) |
| `r_cap` | institutional ceiling on reliance (exam bans, supervision) |
| `a` | how completely AI substitutes for missing capability |

## Status: day-1 results reproduced

- Saddle-node bifurcation confirmed; bistability onset at `kappa* ≈ 0.66`
  for the reference parameter set.
- At `kappa = 0.9`: stable equilibria at `S = 0.004` (trap) and `S = 0.833`
  (healthy), separated by a threshold at `S = 0.303`.
- P/S divergence found in **43.6%** of a 390-point parameter sweep,
  emerging above `kappa ≈ 0.9`.
- Worst case found: measured `P = 0.901` while true `S = 0.006`.

Reproduce: `make day1`

## Layout

```
src/srd/model/      ode, equilibria, bifurcation, observed-performance readout
src/srd/data/       loaders: chess (fit domain), education + colonoscopy (held out)
src/srd/fit/        likelihood, MLE, Bayesian estimation
src/srd/predict/    out-of-sample prediction machinery
src/srd/viz/        phase portraits, bifurcation diagrams
scripts/            numbered, run in order
tests/              pytest
preregistration/    OSF preregistration - LOCK BEFORE STEP 06
paper/              LaTeX
docs/               model spec, 14-day plan
```

## Install (macOS, Apple silicon)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
make test
make day1
```

Everything through step 05 runs on a laptop. Only step 03b (engine analysis of
chess positions) needs a bigger machine — see `docs/compute.md`.

## Licence

MIT (code). Data are under their own licences; see `docs/datasets.md`.
