from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd


def bin_numeric(
    series: pd.Series,
    *,
    bins: int = 10,
    method: str = "quantile",
    labels: Optional[list] = None,
    include_lowest: bool = True,
) -> Tuple[pd.Series, np.ndarray]:
    """Bin numeric series and return (binned, bin_edges)."""
    if method == "quantile":
        binned = pd.qcut(series, q=bins, duplicates="drop", labels=labels)
        bin_edges = binned.cat.categories.left.to_numpy()
    elif method == "uniform":
        binned = pd.cut(series, bins=bins, include_lowest=include_lowest, labels=labels)
        bin_edges = binned.cat.categories.left.to_numpy()
    else:
        raise ValueError("method must be one of: quantile, uniform.")
    return binned, bin_edges


def build_factor_table(
    df: pd.DataFrame,
    *,
    factor_col: str,
    loss_col: str,
    exposure_col: str,
    weight_col: Optional[str] = None,
    base_rate: Optional[float] = None,
    smoothing: float = 0.0,
    min_exposure: Optional[float] = None,
) -> pd.DataFrame:
    """Build a factor table with rate and relativity."""
    if weight_col and weight_col in df.columns:
        weights = df[weight_col].to_numpy(dtype=float, copy=False)
    else:
        weights = None

    loss = df[loss_col].to_numpy(dtype=float, copy=False)
    exposure = df[exposure_col].to_numpy(dtype=float, copy=False)

    if weights is not None:
        loss = loss * weights
        exposure = exposure * weights

    data = pd.DataFrame(
        {
            "factor": df[factor_col],
            "loss": loss,
            "exposure": exposure,
        }
    )
    grouped = data.groupby("factor", dropna=False).agg({"loss": "sum", "exposure": "sum"})
    grouped = grouped.reset_index().rename(columns={"factor": "level"})

    if base_rate is None:
        total_loss = float(grouped["loss"].sum())
        total_exposure = float(grouped["exposure"].sum())
        base_rate = total_loss / total_exposure if total_exposure > 0 else 0.0

    exposure_vals = grouped["exposure"].to_numpy(dtype=float, copy=False)
    loss_vals = grouped["loss"].to_numpy(dtype=float, copy=False)

    with np.errstate(divide="ignore", invalid="ignore"):
        rate = np.where(
            exposure_vals > 0,
            (loss_vals + smoothing * base_rate) / (exposure_vals + smoothing),
            0.0,
        )
        relativity = np.where(base_rate > 0, rate / base_rate, 1.0)

    grouped["rate"] = rate
    grouped["relativity"] = relativity
    grouped["base_rate"] = float(base_rate)

    if min_exposure is not None:
        low_exposure = grouped["exposure"] < float(min_exposure)
        grouped.loc[low_exposure, "relativity"] = 1.0
        grouped.loc[low_exposure, "rate"] = float(base_rate)
        grouped["is_low_exposure"] = low_exposure
    else:
        grouped["is_low_exposure"] = False

    return grouped
