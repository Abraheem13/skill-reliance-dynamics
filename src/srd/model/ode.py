"""Core skill-reliance dynamical system.

State variables
---------------
S : unassisted capability in [0, 1]   -- what the learner can do with AI removed
r : reliance in [0, 1]                -- fraction of cognitive work offloaded to AI

Observed performance P is NOT a state variable; it is a readout (see observed.py).
The central claim of the paper is that P and S can move in opposite directions.
"""
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class Params:
    g: float = 0.40      # practice gain rate (task frequency x instructional quality)
    delta: float = 0.08  # decay / forgetting rate of unassisted capability
    kappa: float = 0.0   # AI capability, relative to learner (drives reliance)
    beta: float = 6.0    # steepness of reliance response (habit formation)
    c: float = 1.0       # suppression of reliance by own capability (self-confidence)
    lam: float = 1.0     # reliance adaptation rate
    r_cap: float = 1.0   # institutional ceiling on reliance (exam bans, supervision)
    a: float = 0.9       # how completely AI substitutes for missing capability

    def to_dict(self):
        return asdict(self)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def dsigmoid(x):
    s = sigmoid(x)
    return s * (1.0 - s)


def reliance_target(S, p):
    """Reliance the learner settles on, given current capability."""
    return p.r_cap * sigmoid(p.beta * (p.kappa - p.c * S))


def rhs(t, y, p):
    """Full two-dimensional vector field."""
    S, r = y
    dS = p.g * (1.0 - r) * (1.0 - S) - p.delta * S
    dr = p.lam * (reliance_target(S, p) - r)
    return np.array([dS, dr])


def reduced_rhs(S, p):
    """Fast-reliance limit (lam >> g). Reliance tracks its target instantly."""
    r = reliance_target(S, p)
    return p.g * (1.0 - r) * (1.0 - S) - p.delta * S


def jacobian(S, r, p):
    """Jacobian of the full system at (S, r)."""
    z = p.beta * (p.kappa - p.c * S)
    return np.array([
        [-p.g * (1.0 - r) - p.delta, -p.g * (1.0 - S)],
        [-p.lam * p.r_cap * dsigmoid(z) * p.beta * p.c, -p.lam],
    ])
