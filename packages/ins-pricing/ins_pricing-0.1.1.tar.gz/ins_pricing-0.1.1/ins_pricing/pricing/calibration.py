from __future__ import annotations

from typing import Optional

import numpy as np


def fit_calibration_factor(
    pred: np.ndarray,
    actual: np.ndarray,
    *,
    weight: Optional[np.ndarray] = None,
    target_lr: Optional[float] = None,
) -> float:
    """Fit a scalar calibration factor for premiums or pure premiums."""
    pred = np.asarray(pred, dtype=float).reshape(-1)
    actual = np.asarray(actual, dtype=float).reshape(-1)
    if weight is not None:
        weight = np.asarray(weight, dtype=float).reshape(-1)
        if weight.shape[0] != pred.shape[0]:
            raise ValueError("weight length must match pred length.")
        pred = pred * weight
        actual = actual * weight

    pred_sum = float(np.sum(pred))
    actual_sum = float(np.sum(actual))
    if pred_sum <= 0:
        return 1.0

    if target_lr is None:
        return actual_sum / pred_sum
    if target_lr <= 0:
        raise ValueError("target_lr must be positive.")
    return actual_sum / (target_lr * pred_sum)


def apply_calibration(pred: np.ndarray, factor: float) -> np.ndarray:
    pred = np.asarray(pred, dtype=float)
    return pred * float(factor)
