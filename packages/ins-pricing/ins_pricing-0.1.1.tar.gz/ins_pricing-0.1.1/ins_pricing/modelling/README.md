# ins_pricing

This directory contains reusable production-grade tooling and training frameworks, with a focus on the BayesOpt series.

Key contents:
- `bayesopt/`: core subpackage (data preprocessing, trainers, models, plotting, explainability)
- `plotting/`: standalone plotting helpers (lift/roc/importance/geo)
- `explain/`: explainability helpers (Permutation/Integrated Gradients/SHAP)
- `BayesOpt.py`: compatibility entry point for legacy imports
- `BayesOpt_entry.py`: batch training CLI
- `BayesOpt_incremental.py`: incremental training CLI
- `cli_common.py` / `notebook_utils.py`: shared CLI and notebook utilities
- `demo/config_template.json` / `demo/config_incremental_template.json`: config templates
- `Explain_entry.py` / `Explain_Run.py`: explainability entry points (load trained models)
- `demo/config_explain_template.json` / `demo/Explain_Run.ipynb`: explainability demo

Note: `modelling/demo/` is kept in the repo only and is not shipped in the PyPI package.

Common usage:
- CLI: `python ins_pricing/modelling/BayesOpt_entry.py --config-json ...`
- Notebook: `from ins_pricing.bayesopt import BayesOptModel`

Explainability (load trained models under `Results/model` and explain a validation set):
- CLI: `python ins_pricing/modelling/Explain_entry.py --config-json ins_pricing/modelling/demo/config_explain_template.json`
- Notebook: open `ins_pricing/modelling/demo/Explain_Run.ipynb` and run it

Notes:
- Models load from `output_dir/model` by default (override with `explain.model_dir`).
- Validation data can be specified via `explain.validation_path`.

Operational notes:
- Training outputs are written to `plot/`, `Results/`, and `model/` by default.
- Keep large data and secrets outside the repo and use environment variables or `.env`.
