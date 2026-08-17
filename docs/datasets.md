# Datasets

## Fit domain — chess
- **Lichess open database** — https://database.lichess.org — CC0, monthly PGN
  dumps. Large (tens of GB/month compressed); sample, do not download all.
- **FIDE rating history** — over-the-board ratings, small and clean, spans the
  engine era. Use for the r_cap-restricted regime.
- Caveat: Elo is relative and inflates. Absolute skill requires engine analysis
  (see `docs/compute.md`).

## Held-out — education
- **PISA 2022** — https://www.oecd.org/pisa — ICT questionnaire + maths/reading.
- **ICILS 2023** — computer and information literacy, cross-national.
- **PIAAC Cycle 2 (2023)** — adult literacy/numeracy, trend to 2012/2017.
- **Published GenAI-in-education studies** — for the H4 test, split by whether
  the outcome was measured with AI present or removed. This split has not been
  separately meta-analysed and is the strongest test in the project.

## Held-out — clinical
- **Budzyń et al. (2025)**, *Lancet Gastroenterol Hepatol* 10(10):896–903,
  DOI 10.1016/S2468-1253(25)00133-5. ADR fell 28.4% → 22.4% after routine AI
  exposure. Published aggregates only unless the authors share patient-level
  data — worth emailing them.

## Honest limitation
No single public dataset measures individual AI use *and* a validated cognitive
outcome longitudinally. This is why the design is model-plus-triangulation
rather than one regression, and it must be stated up front in the paper.
