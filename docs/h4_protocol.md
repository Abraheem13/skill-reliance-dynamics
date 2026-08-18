# H4 screening and coding protocol

## The claim being tested

Studies of generative AI in education that measure outcomes with the AI
REMOVED will report smaller effect sizes than studies measuring outcomes with
the AI PRESENT.

If true, the positive meta-analytic literature (SMD ~0.45) is largely measuring
assisted performance P, not retained capability S - the divergence described
by Proposition 5.

## Search

Databases: Scopus, Web of Science, ERIC, Google Scholar (first 200 hits).
Date range: January 2022 onward.

Query:
  ("generative AI" OR ChatGPT OR "large language model" OR "AI chatbot"
   OR "AI tutor" OR Copilot)
  AND (learning OR education OR student OR achievement)
  AND (experiment OR randomized OR "control group" OR quasi-experimental)

Richest single source: the included-study lists of the existing meta-analyses
(Han et al. 2025, 68 studies; Liu et al. 2025, 37 studies). Those studies are
already screened with effect sizes extracted - you are adding one column.

## Inclusion criteria

Include if ALL hold:
  1. empirical, generative-AI intervention
  2. quantitative learner outcome
  3. comparison group or pre/post design
  4. enough reported to compute a standardised effect size
  5. published 2022 or later

Exclude: opinion pieces, attitude-only outcomes, studies of teachers.

## THE CRITICAL CODING DECISION

Code each effect size as:

  AI_PRESENT   learner had AI access AT THE MOMENT OF MEASUREMENT
  AI_REMOVED   AI withheld at measurement, even if used during learning
  AMBIGUOUS    cannot be determined from the report

Rules:
  * Code from the OUTCOME MEASUREMENT, never the intervention description.
    A study can use AI throughout instruction and still measure AI_REMOVED.
  * "Delayed post-test" does NOT automatically mean AI_REMOVED - check
    whether tool access was actually withheld.
  * If a study reports BOTH, extract both and code separately. These
    within-study pairs are the strongest evidence available.
  * AMBIGUOUS excluded from the primary comparison, kept for sensitivity.

## Reliability

A second coder independently codes a random 20% subsample. Report Cohen's
kappa. If kappa < 0.6, rewrite the rules and recode ALL studies.

## Analysis

Primary:   random-effects meta-regression, condition as moderator.
Secondary: within-study contrasts only (no between-study confounding).
Bias:      funnel plot, Egger's test, trim-and-fill per subgroup.

## Preregistered prediction

Direction: d(AI_REMOVED) < d(AI_PRESENT).
FALSIFIED IF: d(AI_REMOVED) >= d(AI_PRESENT).
If falsified, this is reported as the headline result.
