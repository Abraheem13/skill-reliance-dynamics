# Compute requirements — read before renting a GPU

**You almost certainly do not need a GPU for this project.**

| Step | What it is | Hardware |
|------|-----------|----------|
| 01–03 | ODE solving, root finding, parameter sweeps | M4 Air, seconds |
| 04–05 | Download and parse chess data | M4 Air + disk space |
| 06 | Maximum-likelihood fit | M4 Air, minutes |
| 09 | Bayesian fit (numpyro/MCMC) | M4 Air; more **cores and RAM** help, GPU does not |
| **10** | **Engine analysis of chess positions** | **the one real bottleneck** |

## Step 10 is the only genuine scaling need

Raw Elo cannot measure absolute skill — it is zero-sum and inflates over time.
To show whether human chess strength actually rose or fell across the engine
era you need an *absolute* measure: mean centipawn loss against a strong
engine, per player per year (the Regan & Haworth intrinsic-performance-rating
approach).

That means running Stockfish over millions of positions. It is **CPU-bound and
embarrassingly parallel** — many cores, not a GPU. A 64–128 core box for a few
hours is the right purchase. An H100 would sit idle.

Start on the laptop with a stratified sample (a few thousand games) and confirm
the pipeline works before scaling. If the sampled result is clear, you may not
need the full run at all.
