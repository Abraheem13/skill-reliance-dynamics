"""Observed (assisted) performance readout.

    P = S + a * r * (1 - S)

The learner's measured score is their own capability plus whatever the AI
supplies for the part they cannot do. This is what almost every published
GenAI-in-education effect size actually measures.
"""


def observed_performance(S, r, p):
    return S + p.a * r * (1.0 - S)


def divergence(S, r, p):
    """Gap between what is measured and what the learner actually holds."""
    return observed_performance(S, r, p) - S
