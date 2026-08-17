import numpy as np
import pytest
from dataclasses import replace
from srd.model import Params, rhs, reduced_rhs, reliance_target, observed_performance
from srd.model.equilibria import equilibria, classify
from srd.model.bifurcation import kappa_star, is_bistable

REF = Params(g=0.40, delta=0.08, kappa=0.90, beta=8.0, c=2.0, lam=1.5, r_cap=1.0, a=0.9)


def test_state_space_invariant():
    """S and r must stay in [0,1] under the flow."""
    from scipy.integrate import solve_ivp
    for S0 in [0.0, 0.05, 0.5, 1.0]:
        for r0 in [0.0, 0.5, 1.0]:
            sol = solve_ivp(rhs, (0, 50), [S0, r0], args=(REF,), max_step=0.1)
            assert sol.y.min() >= -1e-6
            assert sol.y.max() <= 1 + 1e-6


def test_no_ai_is_monostable():
    """With no AI available (r_cap=0) there must be exactly one equilibrium."""
    p = replace(REF, r_cap=0.0)
    E = equilibria(p)
    assert len(E) == 1
    assert classify(E[0], p)[0] == "stable"
    # and it should equal the classic learning asymptote g/(g+delta)
    assert E[0] == pytest.approx(p.g / (p.g + p.delta), abs=1e-6)


def test_bistability_appears_above_threshold():
    kstar = kappa_star(REF, -1.0, 2.0, 121)
    assert kstar is not None
    assert not is_bistable(replace(REF, kappa=kstar - 0.15))
    assert is_bistable(replace(REF, kappa=kstar + 0.05))


def test_equilibria_are_roots():
    for S in equilibria(REF):
        assert abs(reduced_rhs(S, REF)) < 1e-8


def test_observed_exceeds_true_capability():
    """P >= S always, with equality only when reliance is zero."""
    for S in np.linspace(0, 1, 11):
        for r in np.linspace(0, 1, 11):
            P = observed_performance(S, r, REF)
            assert P >= S - 1e-12
            if r == 0:
                assert P == pytest.approx(S)


def test_divergence_exists():
    """The paper's central claim must be reproducible."""
    from scipy.integrate import solve_ivp
    p = replace(REF, kappa=0.9)
    sol = solve_ivp(rhs, (0, 60), [0.10, 0.05], args=(p,),
                    dense_output=True, max_step=0.1, rtol=1e-8, atol=1e-10)
    S, r = sol.sol(60.0)
    P = observed_performance(S, r, p)
    assert S < 0.10, "capability should end below where it started"
    assert P > 0.5, "measured performance should look high"
    assert P - S > 0.5, "measured score should badly overstate capability"


def test_institutional_cap_protects():
    """Low r_cap (engines banned, supervised work) should prevent the trap."""
    p = replace(REF, r_cap=0.05)
    assert not is_bistable(p)
    E = equilibria(p)
    assert max(E) > 0.7


# --- analytic propositions -------------------------------------------------

def test_p1_invariance():
    from srd.model import analysis as A
    bf = A.boundary_flow(REF)
    assert bf["S=0"][0] >= -1e-12
    assert bf["S=1"][1] <= 1e-12
    assert bf["r=0"][0] >= -1e-12
    assert bf["r=1"][1] <= 1e-12


def test_p3_necessary_condition_never_violated():
    from srd.model import analysis as A
    rng = np.random.default_rng(1)
    for _ in range(600):
        q = Params(g=rng.uniform(0.05, 1.0), delta=rng.uniform(0.01, 0.5),
                   kappa=rng.uniform(-1, 2), beta=rng.uniform(1, 15),
                   c=rng.uniform(0.2, 4), lam=1.5,
                   r_cap=rng.uniform(0.0, 1.0), a=0.9)
        if is_bistable(q):
            assert A.necessary_condition_holds(q)


def test_p4_transversality_nonzero():
    from srd.model import analysis as A
    ks = kappa_star(REF, -1.0, 2.0, 121)
    assert abs(A.transversality(0.068, replace(REF, kappa=ks))) > 1e-9


def test_p5_divergence_matches_simulation():
    from scipy.integrate import solve_ivp
    from srd.model import analysis as A
    q = replace(REF, kappa=0.9)
    sol = solve_ivp(rhs, (0, 60), [0.10, 0.05], args=(q,), dense_output=True,
                    max_step=0.05, rtol=1e-9, atol=1e-11)
    t = np.linspace(0.01, 60, 500)
    S, r = sol.sol(t)
    for i in range(len(t)):
        _, _, holds = A.divergence_condition(S[i], r[i], q)
        dP = A.dP_dt(S[i], r[i], q)
        dS = q.g * (1 - r[i]) * (1 - S[i]) - q.delta * S[i]
        assert holds == (dP > 0 and dS < 0)
