from __future__ import annotations

from typing import Iterable, Optional

import numpy as np
import pandas as pd


def psi_numeric(
    expected: np.ndarray,
    actual: np.ndarray,
    *,
    bins: int = 10,
    strategy: str = "quantile",
    eps: float = 1e-6,
) -> float:
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    if expected.size == 0 or actual.size == 0:
        return 0.0

    if strategy == "quantile":
        quantiles = np.linspace(0, 1, bins + 1)
        bin_edges = np.quantile(expected, quantiles)
        bin_edges = np.unique(bin_edges)
    elif strategy == "uniform":
        min_val = min(expected.min(), actual.min())
        max_val = max(expected.max(), actual.max())
        bin_edges = np.linspace(min_val, max_val, bins + 1)
    else:
        raise ValueError("strategy must be one of: quantile, uniform.")

    if bin_edges.size < 2:
        return 0.0

    exp_counts, _ = np.histogram(expected, bins=bin_edges)
    act_counts, _ = np.histogram(actual, bins=bin_edges)
    exp_pct = exp_counts / max(exp_counts.sum(), 1)
    act_pct = act_counts / max(act_counts.sum(), 1)
    exp_pct = np.clip(exp_pct, eps, 1.0)
    act_pct = np.clip(act_pct, eps, 1.0)
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def psi_categorical(
    expected: Iterable,
    actual: Iterable,
    *,
    eps: float = 1e-6,
) -> float:
    expected = pd.Series(expected)
    actual = pd.Series(actual)
    categories = pd.Index(expected.dropna().unique()).union(actual.dropna().unique())
    if categories.empty:
        return 0.0
    exp_counts = expected.value_counts().reindex(categories, fill_value=0)
    act_counts = actual.value_counts().reindex(categories, fill_value=0)
    exp_pct = exp_counts / max(exp_counts.sum(), 1)
    act_pct = act_counts / max(act_counts.sum(), 1)
    exp_pct = np.clip(exp_pct.to_numpy(dtype=float), eps, 1.0)
    act_pct = np.clip(act_pct.to_numpy(dtype=float), eps, 1.0)
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def population_stability_index(
    expected: np.ndarray,
    actual: np.ndarray,
    *,
    bins: int = 10,
    strategy: str = "quantile",
) -> float:
    if pd.api.types.is_numeric_dtype(expected) and pd.api.types.is_numeric_dtype(actual):
        return psi_numeric(expected, actual, bins=bins, strategy=strategy)
    return psi_categorical(expected, actual)


def psi_report(
    expected_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    *,
    features: Optional[Iterable[str]] = None,
    bins: int = 10,
    strategy: str = "quantile",
) -> pd.DataFrame:
    feats = list(features) if features is not None else list(expected_df.columns)
    rows = []
    for feat in feats:
        if feat not in expected_df.columns or feat not in actual_df.columns:
            continue
        psi = population_stability_index(
            expected_df[feat].to_numpy(),
            actual_df[feat].to_numpy(),
            bins=bins,
            strategy=strategy,
        )
        rows.append({"feature": feat, "psi": psi})
    return pd.DataFrame(rows).sort_values(by="psi", ascending=False).reset_index(drop=True)
