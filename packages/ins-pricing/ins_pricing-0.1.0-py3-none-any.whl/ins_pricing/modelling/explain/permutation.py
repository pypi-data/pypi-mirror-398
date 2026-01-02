from __future__ import annotations

from typing import Callable, Optional, Sequence

import numpy as np
import pandas as pd

from .metrics import resolve_metric


def _prepare_data(X, y, sample_weight, max_rows, rng):
    y_arr = np.asarray(y)
    if y_arr.ndim != 1:
        y_arr = y_arr.reshape(-1)

    w_arr = None
    if sample_weight is not None:
        w_arr = np.asarray(sample_weight).reshape(-1)
        if w_arr.shape[0] != y_arr.shape[0]:
            raise ValueError("sample_weight length must match y.")

    if isinstance(X, pd.DataFrame):
        X_data = X
        if len(X_data) != len(y_arr):
            raise ValueError("X and y must have the same length.")
        if max_rows and len(X_data) > max_rows:
            idx = rng.choice(len(X_data), size=int(max_rows), replace=False)
            X_data = X_data.iloc[idx].copy()
            y_arr = y_arr[idx]
            if w_arr is not None:
                w_arr = w_arr[idx]
        return X_data, y_arr, w_arr

    X_np = np.asarray(X)
    if X_np.ndim != 2:
        raise ValueError("X must be 2d when not a DataFrame.")
    if X_np.shape[0] != y_arr.shape[0]:
        raise ValueError("X and y must have the same length.")
    if max_rows and X_np.shape[0] > max_rows:
        idx = rng.choice(X_np.shape[0], size=int(max_rows), replace=False)
        X_np = X_np[idx]
        y_arr = y_arr[idx]
        if w_arr is not None:
            w_arr = w_arr[idx]
    return X_np, y_arr, w_arr


def permutation_importance(
    predict_fn: Callable,
    X,
    y,
    *,
    sample_weight=None,
    metric: str | Callable = "auto",
    task_type: Optional[str] = None,
    higher_is_better: Optional[bool] = None,
    n_repeats: int = 5,
    random_state: Optional[int] = None,
    max_rows: Optional[int] = 5000,
    features: Optional[Sequence[str]] = None,
    return_scores: bool = False,
    safe_copy: bool = False,
) -> pd.DataFrame:
    """Permutation importance on tabular data.

    predict_fn should accept the same type as X (DataFrame or ndarray).
    Set safe_copy=True if predict_fn mutates its input.
    """
    rng = np.random.default_rng(random_state)
    n_repeats = max(1, int(n_repeats))

    X_data, y_arr, w_arr = _prepare_data(X, y, sample_weight, max_rows, rng)
    metric_fn, higher_is_better, metric_name = resolve_metric(
        metric, task_type=task_type, higher_is_better=higher_is_better
    )

    baseline_pred = predict_fn(X_data)
    baseline_score = metric_fn(y_arr, baseline_pred, w_arr)

    if isinstance(X_data, pd.DataFrame):
        feature_names = list(X_data.columns)
        if features is not None:
            feature_names = [f for f in features if f in X_data.columns]
        X_perm = X_data.copy()
        results = []
        for feat in feature_names:
            orig_series = X_perm[feat].copy()
            orig_values = orig_series.to_numpy(copy=True)
            scores = []
            for _ in range(n_repeats):
                X_perm[feat] = rng.permutation(orig_values)
                pred_input = X_perm.copy() if safe_copy else X_perm
                pred = predict_fn(pred_input)
                score = metric_fn(y_arr, pred, w_arr)
                scores.append(float(score))
            X_perm[feat] = orig_series

            scores_arr = np.asarray(scores, dtype=float)
            if higher_is_better:
                delta = baseline_score - scores_arr
            else:
                delta = scores_arr - baseline_score
            entry = {
                "feature": feat,
                "importance_mean": float(np.mean(delta)),
                "importance_std": float(np.std(delta)),
                "baseline_score": float(baseline_score),
                "permutation_score_mean": float(np.mean(scores_arr)),
                "metric": metric_name,
            }
            if return_scores:
                entry["permutation_scores"] = scores
            results.append(entry)
    else:
        if features is not None:
            if len(features) != X_data.shape[1]:
                raise ValueError("features length must match X columns for ndarray input.")
            feature_names = list(features)
        else:
            feature_names = [f"x{i}" for i in range(X_data.shape[1])]

        X_base = np.asarray(X_data)
        X_perm = X_base.copy()
        results = []
        for idx, feat in enumerate(feature_names):
            orig_col = X_base[:, idx].copy()
            scores = []
            for _ in range(n_repeats):
                X_perm[:, idx] = rng.permutation(orig_col)
                pred_input = X_perm.copy() if safe_copy else X_perm
                pred = predict_fn(pred_input)
                score = metric_fn(y_arr, pred, w_arr)
                scores.append(float(score))
            X_perm[:, idx] = orig_col

            scores_arr = np.asarray(scores, dtype=float)
            if higher_is_better:
                delta = baseline_score - scores_arr
            else:
                delta = scores_arr - baseline_score
            entry = {
                "feature": feat,
                "importance_mean": float(np.mean(delta)),
                "importance_std": float(np.std(delta)),
                "baseline_score": float(baseline_score),
                "permutation_score_mean": float(np.mean(scores_arr)),
                "metric": metric_name,
            }
            if return_scores:
                entry["permutation_scores"] = scores
            results.append(entry)

    df = pd.DataFrame(results)
    df = df.sort_values(by="importance_mean", ascending=False).reset_index(drop=True)
    return df
