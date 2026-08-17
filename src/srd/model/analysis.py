"""Analytic results for the skill-reliance system.

Each function corresponds to a proposition in docs/model_spec.md and is
checked numerically by scripts/04_verify_propositions.py.
"""
import numpy as np
from .ode import Params, sigmoid, dsigmoid, reliance_target, reduced_rhs


# --- Proposition 1: forward invariance of the unit square ------------------

def boundary_flow(p):
    """Sign of the vector field on each edge of [0,1]^2."""
    grid = np.linspace(0.0, 1.0, 401)
    out = {}
    out["S=0"] = (min(p.g * (1 - r) for r in grid), max(p.g * (1 - r) for r in grid))
    out["S=1"] = (-p.delta, -p.delta)
    out["r=0"] = (min(p.lam * reliance_target(S, p) for S in grid),
                  max(p.lam * reliance_target(S, p) for S in grid))
    out["r=1"] = (min(p.lam * (reliance_target(S, p) - 1) for S in grid),
                  max(p.lam * (reliance_target(S, p) - 1) for S in grid))
    return out


# --- Proposition 2: the no-AI baseline -------------------------------------

def baseline_equilibrium(p):
    """With r_cap = 0, dS/dt = g(1-S) - delta*S has unique root g/(g+delta)."""
    return p.g / (p.g + p.delta)


# --- Proposition 3: necessary condition for bistability --------------------

def loop_gain(p):
    """Positive-feedback loop gain: beta * c * r_cap."""
    return p.beta * p.c * p.r_cap


def bistability_bound(p):
    """Right-hand side of the necessary condition, 4*delta/g."""
    return 4.0 * p.delta / p.g


def necessary_condition_holds(p):
    """Proposition 3. Bistability implies beta*c*r_cap > 4*delta/g.

    F'(S) = g*r_cap*beta*c*s(1-s)*(1-S) - g(1-r(S)) - delta,  s = sigmoid(z).
    Three equilibria need F'(S) > 0 somewhere. Since s(1-s) <= 1/4,
    (1-S) <= 1 and g(1-r) >= 0:  F'(S) <= g*r_cap*beta*c/4 - delta.
    NECESSARY, NOT SUFFICIENT.
    """
    return loop_gain(p) > bistability_bound(p)


def F_prime(S, p):
    """Derivative of the reduced vector field (tangency condition)."""
    z = p.beta * (p.kappa - p.c * S)
    s = sigmoid(z)
    r = p.r_cap * s
    return p.g * p.r_cap * p.beta * p.c * s * (1 - s) * (1 - S) - p.g * (1 - r) - p.delta


# --- Proposition 4: the bifurcation is a genuine saddle-node ---------------

def transversality(S, p):
    """dF/dkappa at a fold. Non-zero => saddle-node, not degenerate."""
    z = p.beta * (p.kappa - p.c * S)
    s = sigmoid(z)
    return -p.g * (1 - S) * p.r_cap * p.beta * s * (1 - s)


def fold_residual(S, p):
    """Both components vanish exactly at a fold: F(S)=0 and F'(S)=0."""
    return np.array([reduced_rhs(S, p), F_prime(S, p)])


# --- Proposition 5: the divergence condition -------------------------------

def divergence_condition(S, r, p):
    """Measured performance rises while capability falls iff

        a(1-S)*dr/dt > (1 - a*r)*|dS/dt|,  with dS/dt < 0.

    Since P = S + a*r*(1-S):
        dP/dt = (1 - a*r)*dS/dt + a*(1-S)*dr/dt.
    """
    dS = p.g * (1 - r) * (1 - S) - p.delta * S
    dr = p.lam * (reliance_target(S, p) - r)
    lhs = p.a * (1 - S) * dr
    rhs = (1 - p.a * r) * abs(dS)
    return lhs, rhs, bool(dS < 0 and lhs > rhs)


def dP_dt(S, r, p):
    dS = p.g * (1 - r) * (1 - S) - p.delta * S
    dr = p.lam * (reliance_target(S, p) - r)
    return (1 - p.a * r) * dS + p.a * (1 - S) * dr
