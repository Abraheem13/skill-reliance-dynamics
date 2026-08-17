.PHONY: test day1 clean figures

test:
	PYTHONPATH=src python3 -m pytest -q

day1:
	PYTHONPATH=src python3 scripts/01_derive_equilibria.py
	PYTHONPATH=src python3 scripts/02_bifurcation_scan.py
	PYTHONPATH=src python3 scripts/03_divergence_sweep.py
	PYTHONPATH=src python3 scripts/04_verify_propositions.py

figures:
	PYTHONPATH=src python3 scripts/09_make_figures.py

clean:
	rm -rf __pycache__ .pytest_cache
	find . -name "*.pyc" -delete
