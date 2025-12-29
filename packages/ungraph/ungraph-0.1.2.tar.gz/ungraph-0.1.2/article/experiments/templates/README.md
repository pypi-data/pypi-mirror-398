# Experiments templates

This folder contains configuration templates for reproducible experiments.

- `opik_template.yaml`: generic Opik experiment config template.
- `finance_eti_v1.yaml`: example config for a small finance ETI demo (mock inference by default).

Usage:
- Copy a template to `experiments/<your_experiment>/` and fill the fields.
- Do NOT store secrets in repository; use environment variables (e.g. `OPIK_API_KEY`).