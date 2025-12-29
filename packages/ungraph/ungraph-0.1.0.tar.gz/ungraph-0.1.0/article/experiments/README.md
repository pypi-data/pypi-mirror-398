# Experiments — Reproducibility

This folder contains templates and examples for running reproducible experiments.

Demo (finance):
- Config: `project/experiments/finance_demo/opik_config.yaml`
- Runner: `project/experiments/finance_demo/run_finance_demo.py` (wraps `scripts/run_experiment.py`)

To reproduce the demo locally (mock inference):
1. Activate the project's venv: `D:/projects/Ungraph/.venv/Scripts/Activate.ps1` (PowerShell)
2. Install requirements: `pip install -r requirements.txt` (or `pip install pyyaml numpy scikit-learn seaborn nbclient joblib matplotlib`)
3. Run: `python project/experiments/finance_demo/run_finance_demo.py --nb-samples 10 --out experiments/finance_demo_run1`

Notes:
- For real LM-backed runs, set environment variable `OPIK_API_KEY` and update the `opik.model` in the config.
- All runs produce `metadata.json` and a `prov_bundle.json` for traceability; do not publish secrets in repos.
