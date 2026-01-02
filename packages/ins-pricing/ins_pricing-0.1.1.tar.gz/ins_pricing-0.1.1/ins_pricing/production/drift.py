from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd

try:
    from ins_pricing.pricing.monitoring import psi_report as _psi_report
except Exception:  # pragma: no cover - optional import
    _psi_report = None


def psi_report(
    expected_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    *,
    features: Optional[Iterable[str]] = None,
    bins: int = 10,
    strategy: str = "quantile",
) -> pd.DataFrame:
    """Population Stability Index report for drift monitoring."""
    if _psi_report is None:
        raise RuntimeError("psi_report requires ins_pricing.pricing.monitoring.")
    return _psi_report(
        expected_df,
        actual_df,
        features=features,
        bins=bins,
        strategy=strategy,
    )
