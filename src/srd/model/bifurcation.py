"""Locate the saddle-node (tipping point) in AI capability kappa."""
import numpy as np
from dataclasses import replace
from .equilibria import equilibria, stable_equilibria


def n_stable(kappa, p):
    return len(stable_equilibria(replace(p, kappa=kappa)))


def scan_kappa(p, lo=-3.0, hi=3.0, n=241):
    """Return (kappa grid, list of equilibria, count of stable equilibria)."""
    ks = np.linspace(lo, hi, n)
    eqs, ns = [], []
    for k in ks:
        pk = replace(p, kappa=k)
        eqs.append(equilibria(pk))
        ns.append(len(stable_equilibria(pk)))
    return ks, eqs, np.array(ns)


def kappa_star(p, lo=-3.0, hi=3.0, n=241, refine=40):
    """Smallest kappa at which a second stable equilibrium appears (bistability onset).

    Returns None if the system is monostable across the whole scanned range.
    """
    ks, _, ns = scan_kappa(p, lo, hi, n)
    idx = np.where(ns >= 2)[0]
    if idx.size == 0:
        return None
    i = idx[0]
    a, b = ks[max(i - 1, 0)], ks[i]
    for _ in range(refine):          # bisection on the count
        m = 0.5 * (a + b)
        if n_stable(m, p) >= 2:
            b = m
        else:
            a = m
    return 0.5 * (a + b)


def is_bistable(p):
    return len(stable_equilibria(p)) >= 2
