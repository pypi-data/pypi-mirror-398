# Ins-Pricing Overview

This repository contains risk modeling and optimization notebooks, scripts, and a reusable training framework. The main module is `ins_pricing/modelling/bayesopt`.

## Top-level structure

- `Auto Info/`: vehicle info crawling, preprocessing, and embedding experiments
- `GLM and LGB/`: GLM/LightGBM modeling experiments
- `OpenAI/`: OpenAI notebook prototypes
- `Python Code/`: runnable scripts and utilities
- `others/`: temporary or miscellaneous notebooks
- `ins_pricing/`: reusable training framework and CLI tools (BayesOpt subpackage)
- `user_packages legacy/`: historical snapshot

Note: `ins_pricing/modelling/demo/` is kept in the repo only and is not shipped in the PyPI package.

## Quickstart

Run the following commands from the repo root:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\\.venv\\Scripts\\activate
pip install pandas scikit-learn lightgbm seaborn matplotlib
```

Start notebooks:

```bash
jupyter lab
```

## BayesOpt entry points

- CLI batch training: `python ins_pricing/modelling/BayesOpt_entry.py --config-json <path>`
- Incremental training: `python ins_pricing/modelling/BayesOpt_incremental.py --config-json <path>`
- Python API: `from ins_pricing.modelling import BayesOptModel`

## Tests

```bash
pytest -q
```

## Data and outputs

- Put shared data under `data/` (create it if needed).
- Training outputs are written to `plot/`, `Results/`, and `model/` by default.
- Keep secrets and large files outside the repo and use environment variables or `.env`.
