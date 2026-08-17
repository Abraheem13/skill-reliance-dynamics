# 14-day plan

Everything through day 9 runs on the MacBook. Day 10 is the first point where
more compute genuinely helps.

| Day | Task | Deliverable | Kill criterion |
|-----|------|-------------|----------------|
| 1 | Model spec, equilibria, stability | `scripts/01`, tests pass | — |
| 2 | Bifurcation, locate κ* | `scripts/02` | no bifurcation → drop H1, narrow paper |
| 3 | Divergence sweep | `scripts/03` | empty region → **project pivots** |
| 4 | Analytic proof of the tipping condition | `docs/model_spec.md` | can't prove → keep numerical only |
| 5 | Write + post preregistration | OSF DOI | **DRAFTED — post before day 6** |
| 6 | Chess data acquisition | `scripts/04` | — |
| 7 | Build player-year panel | `scripts/05` | — |
| 8 | Fit model (MLE) | `results/fits/` | won't identify → simplify model |
| 9 | Bayesian fit + sensitivity | posterior | — |
| 10 | **Engine analysis at scale** (if needed) | centipawn-loss series | — |
| 11 | Held-out prediction: education | `scripts/07` | — |
| 12 | Held-out prediction: colonoscopy | `scripts/07` | wrong sign → report as falsification |
| 13 | Figures | `results/figures/` | — |
| 14 | Draft methods + results | `paper/` | — |

## Day 3 is the real decision point

If the divergence region is empty, the paper's central claim is dead and you
should stop and rethink rather than push on. (As of the day-1 run it is not
empty — 43.6% of the sampled space — so this gate is currently passed.)
