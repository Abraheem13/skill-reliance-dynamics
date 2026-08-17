# Model specification and analytic results

Fast-reliance reduction: r(S) = r_cap * sigma(beta(kappa - cS)), and

    F(S) = g(1 - r(S))(1 - S) - delta*S
    P    = S + a*r*(1 - S)

## Proposition 1 - forward invariance

[0,1]^2 is forward invariant.

Proof. On S=0, dS/dt = g(1-r) >= 0. On S=1, dS/dt = -delta < 0. On r=0,
dr/dt = lam*r_cap*sigma >= 0. On r=1, dr/dt = lam(r_cap*sigma - 1) <= 0 since
r_cap <= 1. No trajectory leaves through any edge. QED

## Proposition 2 - the no-AI baseline

With r_cap = 0 the unique, globally stable equilibrium is S* = g/(g+delta).

Proof. F(S) = g(1-S) - delta*S is affine with slope -(g+delta) < 0, so it has
one root, at g/(g+delta). QED

This is the counterfactual the paper is measured against. For the reference
parameters S* = 0.833 - exactly the healthy equilibrium the full system retains
when AI is present but restricted.

## Proposition 3 - necessary condition for bistability

Bistability requires  beta * c * r_cap  >  4*delta/g.

Proof. F'(S) = g*r_cap*beta*c*s(1-s)(1-S) - g(1-r(S)) - delta, with
s = sigma(beta(kappa - cS)). Three equilibria require F'(S) > 0 somewhere.
Since s(1-s) <= 1/4, (1-S) <= 1 and g(1-r) >= 0,
    F'(S) <= g*r_cap*beta*c/4 - delta,
so F'(S) > 0 forces beta*c*r_cap > 4*delta/g. QED

NECESSARY, NOT SUFFICIENT - 0 counterexamples in 4000 random draws, but the
bound is not tight.

Interpretation: the left side is the loop gain; the right side is forgetting
over learning. r_cap enters multiplicatively, which is why restricting AI
during assessment is the most effective intervention the model admits.

## Proposition 4 - the fold is a genuine saddle-node

At the fold F(S)=0 and F'(S)=0, and
    dF/dkappa = -g(1-S)*r_cap*beta*s(1-s) < 0  for S < 1.
Transversality holds, so by the implicit function theorem the bifurcation is a
non-degenerate saddle-node. QED

Verified: kappa* = 0.662570, fold at S = 0.068, residuals ~1e-9 and ~5e-13,
dF/dkappa = -0.0429.

## Proposition 5 - the divergence condition

Since P = S + a*r*(1-S),
    dP/dt = (1 - a*r)*dS/dt + a*(1-S)*dr/dt
Measured performance rises while capability falls exactly when
    dS/dt < 0   and   a(1-S)*dr/dt > (1 - a*r)*|dS/dt|

Both terms are largest when S is low - precisely a child early in acquisition.
QED

Verified: agrees with simulation at 4000/4000 sampled points; the reference
trajectory spends 25.1% of its time in the divergent regime.

## What these do and do not establish

These are theorems about the model, under its assumptions. They do not prove
anything about children. Their value is that they generate predictions which
can be checked against data - and which can fail.
