"""Fixed points of the reduced system and their stability."""
import numpy as np
from scipy.optimize import brentq
from .ode import reduced_rhs, reliance_target, jacobian


def equilibria(p, n_grid=2001, tol=1e-10):
    """All roots of reduced_rhs on [0, 1], found by sign-change bracketing."""
    xs = np.linspace(0.0, 1.0, n_grid)
    fs = np.array([reduced_rhs(x, p) for x in xs])
    roots = []
    for i in range(n_grid - 1):
        if fs[i] == 0.0:
            roots.append(xs[i])
        elif fs[i] * fs[i + 1] < 0.0:
            roots.append(brentq(reduced_rhs, xs[i], xs[i + 1], args=(p,), xtol=tol))
    # de-duplicate
    out = []
    for x in sorted(roots):
        if not out or abs(x - out[-1]) > 1e-7:
            out.append(x)
    return out


def classify(S, p):
    """Return ('stable'|'unstable'|'saddle', eigenvalues) for the full 2-D system."""
    r = reliance_target(S, p)
    J = jacobian(S, r, p)
    ev = np.linalg.eigvals(J)
    re = ev.real
    if np.all(re < 0):
        kind = "stable"
    elif np.all(re > 0):
        kind = "unstable"
    else:
        kind = "saddle"
    return kind, ev


def stable_equilibria(p):
    return [S for S in equilibria(p) if classify(S, p)[0] == "stable"]
