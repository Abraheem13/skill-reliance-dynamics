"""Build the player-year panel the model is fitted to."""
from __future__ import annotations
import pandas as pd
import numpy as np

MIN_POSITIONS_PER_GAME = 8     # below this, per-game ACPL is noise
MIN_POSITIONS_PER_YEAR = 150
MIN_GAMES_PER_YEAR = 6


def games_to_long(rows: list) -> pd.DataFrame:
    out = []
    for r in rows:
        if not r:
            continue
        year = None
        d = r.get("date")
        if d:
            year = int(str(d)[:4])
        for side in ("white", "black"):
            acpl = r.get(f"{side}_acpl")
            n = r.get(f"{side}_n_positions") or 0
            if acpl is None or n < MIN_POSITIONS_PER_GAME:
                continue
            try:
                elo = int(r.get(f"{side}_elo") or 0)
            except ValueError:
                elo = 0
            ev = (r.get("event") or "").lower()
            perf = ("bullet" if "bullet" in ev else
                    "blitz" if "blitz" in ev else
                    "rapid" if "rapid" in ev else
                    "classical" if "classical" in ev else "other")
            out.append(dict(player=r.get(side), year=year, acpl=float(acpl),
                            n_positions=int(n), elo=elo, perf=perf,
                            engine_depth=r.get("engine_depth")))
    return pd.DataFrame(out)


def build_panel(long_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to player-year, weighting ACPL by positions analysed."""
    if long_df.empty:
        return long_df
    g = long_df.groupby(["player", "year", "perf"], dropna=True)
    panel = g.apply(lambda d: pd.Series({
        "acpl": np.average(d["acpl"], weights=d["n_positions"]),
        "n_positions": d["n_positions"].sum(),
        "n_games": len(d),
        "elo": d["elo"].mean(),
    }), include_groups=False).reset_index()
    panel = panel[(panel.n_positions >= MIN_POSITIONS_PER_YEAR) &
                  (panel.n_games >= MIN_GAMES_PER_YEAR)]
    return panel.reset_index(drop=True)


def within_player(panel):
    """Keep only players observed in 2+ years. This is the primary sample."""
    counts = panel.groupby(["player", "perf"])["year"].nunique()
    keep = set(counts[counts >= 2].index)
    mask = [(p_, f_) in keep for p_, f_ in zip(panel.player, panel.perf)]
    return panel[mask].reset_index(drop=True)


def acpl_to_capability(panel: pd.DataFrame, lo: float = 10.0, hi: float = 120.0) -> pd.DataFrame:
    """Map ACPL onto the model's S in [0,1]. Lower ACPL = higher capability.

    lo/hi are FIXED reference points declared in advance, not fitted, so S is
    comparable across years. Values outside are clipped.
    """
    p = panel.copy()
    p["S"] = 1.0 - (p["acpl"].clip(lo, hi) - lo) / (hi - lo)
    return p
