# Ins-Pricing

Distribution name: Ins-Pricing (import package is `ins_pricing`, legacy alias `user_packages` still works).

Reusable modelling and pricing utilities organized as a small toolbox with clear boundaries
between modelling, production, governance, and reporting.

## Architecture

- `modelling/`
  - `bayesopt/`: BayesOpt training core (GLM / XGB / ResNet / FT / GNN).
  - `plotting/`: model-agnostic curves and geo visualizations.
  - `explain/`: permutation, gradients, and SHAP helpers.
  - `BayesOpt_entry.py`: CLI runner for batch training.
  - `BayesOpt_incremental.py`: CLI for incremental runs.
  - `Pricing_Run.py`: lightweight pricing orchestration.
- `pricing/`: factor tables, calibration, exposure, monitoring.
- `production/`: scoring, metrics, drift/PSI.
- `governance/`: registry, release, audit, approval workflow.
- `reporting/`: report builder + scheduler.

## Call flow (typical)

1. Model training
   - Python API: `from ins_pricing.modelling import BayesOptModel`
   - CLI: `python ins_pricing/modelling/BayesOpt_entry.py --config-json ...`
2. Evaluation & visualization
   - Curves: `from ins_pricing.plotting import curves`
   - Importance: `from ins_pricing.plotting import importance`
   - Geo: `from ins_pricing.plotting import geo`
3. Explainability
   - `from ins_pricing.explain import permutation_importance, integrated_gradients_torch`
4. Pricing loop
   - `from ins_pricing.pricing import build_factor_table, rate_premium`
5. Production & governance
   - `from ins_pricing.production import batch_score, psi_report`
   - `from ins_pricing.governance import ModelRegistry, ReleaseManager`
6. Reporting
   - `from ins_pricing.reporting import build_report, write_report, schedule_daily`

## Import notes

- `ins_pricing` exposes lightweight lazy imports so that `pricing/production/governance`
  can be used without installing heavy ML dependencies.
- Demo notebooks/configs live in the repo under `ins_pricing/modelling/demo/` and are not shipped in the PyPI package.
- Heavy dependencies are only required when you import or use the related modules:
  - BayesOpt: `torch`, `optuna`, `xgboost`, etc.
  - Explain: `torch` (gradients), `shap` (SHAP).
  - Geo plotting on basemap: `contextily`.
  - Plotting: `matplotlib`.

## Backward-compatible imports

Legacy import paths continue to work:

- `import user_packages`
- `import user_packages.bayesopt`
- `import user_packages.plotting`
- `import user_packages.explain`
- `import user_packages.BayesOpt`
