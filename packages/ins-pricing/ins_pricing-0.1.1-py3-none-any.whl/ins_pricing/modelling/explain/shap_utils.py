from __future__ import annotations

from typing import Callable, Optional

import numpy as np
import pandas as pd


def _require_shap():
    try:
        import shap  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError("SHAP is required. Install with `pip install shap`.") from exc
    return shap


def compute_shap_core(
    ctx,
    model_key: str,
    n_background: int,
    n_samples: int,
    on_train: bool,
    X_df: pd.DataFrame,
    prep_fn: Callable[[pd.DataFrame], np.ndarray],
    predict_fn: Callable[[np.ndarray], np.ndarray],
    cleanup_fn: Optional[Callable[[], None]] = None,
) -> dict:
    """Shared SHAP pipeline using KernelExplainer with lazy import."""
    _ = on_train
    if model_key not in ctx.trainers or ctx.trainers[model_key].model is None:
        raise RuntimeError(f"Model {model_key} not trained.")
    if cleanup_fn:
        cleanup_fn()
    shap = _require_shap()
    bg_df = ctx._sample_rows(X_df, n_background)
    bg_mat = prep_fn(bg_df)
    explainer = shap.KernelExplainer(predict_fn, bg_mat)
    ex_df = ctx._sample_rows(X_df, n_samples)
    ex_mat = prep_fn(ex_df)
    nsample_eff = ctx._shap_nsamples(ex_mat)
    shap_values = explainer.shap_values(ex_mat, nsamples=nsample_eff)
    bg_pred = predict_fn(bg_mat)
    base_value = float(np.asarray(bg_pred).mean())

    return {
        "explainer": explainer,
        "X_explain": ex_df,
        "shap_values": shap_values,
        "base_value": base_value,
    }


def compute_shap_glm(ctx, n_background: int = 500, n_samples: int = 200, on_train: bool = True):
    data = ctx.train_oht_scl_data if on_train else ctx.test_oht_scl_data
    design_all = ctx._build_glm_design(data)
    design_cols = list(design_all.columns)

    def predict_wrapper(x_np):
        x_df = pd.DataFrame(x_np, columns=design_cols)
        y_pred = ctx.glm_best.predict(x_df)
        return np.asarray(y_pred, dtype=np.float64).reshape(-1)

    return compute_shap_core(
        ctx,
        "glm",
        n_background,
        n_samples,
        on_train,
        X_df=design_all,
        prep_fn=lambda df: df.to_numpy(dtype=np.float64),
        predict_fn=predict_wrapper,
    )


def compute_shap_xgb(ctx, n_background: int = 500, n_samples: int = 200, on_train: bool = True):
    data = ctx.train_data if on_train else ctx.test_data
    X_raw = data[ctx.factor_nmes]

    def predict_wrapper(x_mat):
        df_input = ctx._decode_ft_shap_matrix_to_df(x_mat)
        return ctx.xgb_best.predict(df_input)

    return compute_shap_core(
        ctx,
        "xgb",
        n_background,
        n_samples,
        on_train,
        X_df=X_raw,
        prep_fn=lambda df: ctx._build_ft_shap_matrix(df).astype(np.float64),
        predict_fn=predict_wrapper,
    )


def compute_shap_resn(ctx, n_background: int = 500, n_samples: int = 200, on_train: bool = True):
    data = ctx.train_oht_scl_data if on_train else ctx.test_oht_scl_data
    X = data[ctx.var_nmes]

    def cleanup():
        import torch

        ctx.resn_best.device = torch.device("cpu")
        ctx.resn_best.resnet.to("cpu")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return compute_shap_core(
        ctx,
        "resn",
        n_background,
        n_samples,
        on_train,
        X_df=X,
        prep_fn=lambda df: df.to_numpy(dtype=np.float64),
        predict_fn=lambda x: ctx._resn_predict_wrapper(x),
        cleanup_fn=cleanup,
    )


def compute_shap_ft(ctx, n_background: int = 500, n_samples: int = 200, on_train: bool = True):
    if str(ctx.config.ft_role) != "model":
        raise RuntimeError(
            "FT is configured as embedding-only (ft_role != 'model'); FT SHAP is disabled."
        )
    data = ctx.train_data if on_train else ctx.test_data
    X_raw = data[ctx.factor_nmes]

    def cleanup():
        import torch

        ctx.ft_best.device = torch.device("cpu")
        ctx.ft_best.ft.to("cpu")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return compute_shap_core(
        ctx,
        "ft",
        n_background,
        n_samples,
        on_train,
        X_df=X_raw,
        prep_fn=lambda df: ctx._build_ft_shap_matrix(df).astype(np.float64),
        predict_fn=ctx._ft_shap_predict_wrapper,
        cleanup_fn=cleanup,
    )
