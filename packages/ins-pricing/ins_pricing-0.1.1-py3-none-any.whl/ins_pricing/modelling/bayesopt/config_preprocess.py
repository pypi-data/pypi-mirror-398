from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from .utils import IOUtils

# NOTE: Some CSV exports may contain invisible BOM characters or leading/trailing
# spaces in column names. Pandas requires exact matches, so we normalize a few
# "required" column names (response/weight/binary response) before validating.


def _clean_column_name(name: Any) -> Any:
    if not isinstance(name, str):
        return name
    return name.replace("\ufeff", "").strip()


def _normalize_required_columns(
    df: pd.DataFrame, required: List[Optional[str]], *, df_label: str
) -> None:
    required_names = [r for r in required if isinstance(r, str) and r.strip()]
    if not required_names:
        return

    mapping: Dict[Any, Any] = {}
    existing = set(df.columns)
    for col in df.columns:
        cleaned = _clean_column_name(col)
        if cleaned != col and cleaned not in existing:
            mapping[col] = cleaned
    if mapping:
        df.rename(columns=mapping, inplace=True)

    existing = set(df.columns)
    for req in required_names:
        if req in existing:
            continue
        candidates = [
            col
            for col in df.columns
            if isinstance(col, str) and _clean_column_name(col).lower() == req.lower()
        ]
        if len(candidates) == 1 and req not in existing:
            df.rename(columns={candidates[0]: req}, inplace=True)
            existing = set(df.columns)
        elif len(candidates) > 1:
            raise KeyError(
                f"{df_label} has multiple columns matching required {req!r} "
                f"(case/space-insensitive): {candidates}"
            )


# ===== Core components and training wrappers =================================

# =============================================================================
# Config, preprocessing, and trainer base types
# =============================================================================
@dataclass
class BayesOptConfig:
    model_nme: str
    resp_nme: str
    weight_nme: str
    factor_nmes: List[str]
    task_type: str = 'regression'
    binary_resp_nme: Optional[str] = None
    cate_list: Optional[List[str]] = None
    prop_test: float = 0.25
    rand_seed: Optional[int] = None
    epochs: int = 100
    use_gpu: bool = True
    xgb_max_depth_max: int = 25
    xgb_n_estimators_max: int = 500
    use_resn_data_parallel: bool = False
    use_ft_data_parallel: bool = False
    use_resn_ddp: bool = False
    use_ft_ddp: bool = False
    use_gnn_data_parallel: bool = False
    use_gnn_ddp: bool = False
    gnn_use_approx_knn: bool = True
    gnn_approx_knn_threshold: int = 50000
    gnn_graph_cache: Optional[str] = None
    gnn_max_gpu_knn_nodes: Optional[int] = 200000
    gnn_knn_gpu_mem_ratio: float = 0.9
    gnn_knn_gpu_mem_overhead: float = 2.0
    region_province_col: Optional[str] = None  # Province column for hierarchical smoothing
    region_city_col: Optional[str] = None      # City column for hierarchical smoothing
    region_effect_alpha: float = 50.0          # Smoothing strength (pseudo sample size)
    geo_feature_nmes: Optional[List[str]] = None  # Columns for geo tokens; None disables GNN
    geo_token_hidden_dim: int = 32
    geo_token_layers: int = 2
    geo_token_dropout: float = 0.1
    geo_token_k_neighbors: int = 10
    geo_token_learning_rate: float = 1e-3
    geo_token_epochs: int = 50
    output_dir: Optional[str] = None
    optuna_storage: Optional[str] = None
    optuna_study_prefix: Optional[str] = None
    best_params_files: Optional[Dict[str, str]] = None
    # FT roles:
    #   - "model": FT is a standalone predictor (keep lift/SHAP evaluation)
    #   - "embedding": FT only exports embeddings as downstream features
    #   - "unsupervised_embedding": masked reconstruction pretraining + embeddings
    ft_role: str = "model"
    ft_feature_prefix: str = "ft_emb"
    ft_num_numeric_tokens: Optional[int] = None
    reuse_best_params: bool = False
    resn_weight_decay: float = 1e-4
    final_ensemble: bool = False
    final_ensemble_k: int = 3
    final_refit: bool = True


class OutputManager:
    # Centralize output paths for plots, results, and models.

    def __init__(self, root: Optional[str] = None, model_name: str = "model") -> None:
        self.root = Path(root or os.getcwd())
        self.model_name = model_name
        self.plot_dir = self.root / 'plot'
        self.result_dir = self.root / 'Results'
        self.model_dir = self.root / 'model'

    def _prepare(self, path: Path) -> str:
        IOUtils.ensure_parent_dir(str(path))
        return str(path)

    def plot_path(self, filename: str) -> str:
        return self._prepare(self.plot_dir / filename)

    def result_path(self, filename: str) -> str:
        return self._prepare(self.result_dir / filename)

    def model_path(self, filename: str) -> str:
        return self._prepare(self.model_dir / filename)


class VersionManager:
    """Lightweight versioning: save config and best-params snapshots for traceability."""

    def __init__(self, output: OutputManager) -> None:
        self.output = output
        self.version_dir = Path(self.output.result_dir) / "versions"
        IOUtils.ensure_parent_dir(str(self.version_dir))

    def save(self, tag: str, payload: Dict[str, Any]) -> str:
        safe_tag = tag.replace(" ", "_")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.version_dir / f"{ts}_{safe_tag}.json"
        IOUtils.ensure_parent_dir(str(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        print(f"[Version] Saved snapshot: {path}")
        return str(path)

    def load_latest(self, tag: str) -> Optional[Dict[str, Any]]:
        """Load the latest snapshot for a tag (sorted by timestamp prefix)."""
        safe_tag = tag.replace(" ", "_")
        pattern = f"*_{safe_tag}.json"
        candidates = sorted(self.version_dir.glob(pattern))
        if not candidates:
            return None
        path = candidates[-1]
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[Version] Failed to load snapshot {path}: {exc}")
            return None


class DatasetPreprocessor:
    # Prepare shared train/test views for trainers.

    def __init__(self, train_df: pd.DataFrame, test_df: pd.DataFrame,
                 config: BayesOptConfig) -> None:
        self.config = config
        self.train_data = train_df.copy(deep=True)
        self.test_data = test_df.copy(deep=True)
        self.num_features: List[str] = []
        self.train_oht_data: Optional[pd.DataFrame] = None
        self.test_oht_data: Optional[pd.DataFrame] = None
        self.train_oht_scl_data: Optional[pd.DataFrame] = None
        self.test_oht_scl_data: Optional[pd.DataFrame] = None
        self.var_nmes: List[str] = []
        self.cat_categories_for_shap: Dict[str, List[Any]] = {}

    def run(self) -> "DatasetPreprocessor":
        """Run preprocessing: categorical encoding, target clipping, numeric scaling."""
        cfg = self.config
        _normalize_required_columns(
            self.train_data,
            [cfg.resp_nme, cfg.weight_nme, cfg.binary_resp_nme],
            df_label="Train data",
        )
        _normalize_required_columns(
            self.test_data,
            [cfg.resp_nme, cfg.weight_nme, cfg.binary_resp_nme],
            df_label="Test data",
        )
        missing_train = [
            col for col in (cfg.resp_nme, cfg.weight_nme)
            if col not in self.train_data.columns
        ]
        if missing_train:
            raise KeyError(
                f"Train data missing required columns: {missing_train}. "
                f"Available columns (first 50): {list(self.train_data.columns)[:50]}"
            )
        if cfg.binary_resp_nme and cfg.binary_resp_nme not in self.train_data.columns:
            raise KeyError(
                f"Train data missing binary response column: {cfg.binary_resp_nme}. "
                f"Available columns (first 50): {list(self.train_data.columns)[:50]}"
            )

        test_has_resp = cfg.resp_nme in self.test_data.columns
        test_has_weight = cfg.weight_nme in self.test_data.columns
        test_has_binary = bool(
            cfg.binary_resp_nme and cfg.binary_resp_nme in self.test_data.columns
        )
        if not test_has_weight:
            self.test_data[cfg.weight_nme] = 1.0
        if not test_has_resp:
            self.test_data[cfg.resp_nme] = np.nan
        if cfg.binary_resp_nme and cfg.binary_resp_nme not in self.test_data.columns:
            self.test_data[cfg.binary_resp_nme] = np.nan

        # Precompute weighted actuals for plots and validation checks.
        self.train_data.loc[:, 'w_act'] = self.train_data[cfg.resp_nme] * \
            self.train_data[cfg.weight_nme]
        if test_has_resp:
            self.test_data.loc[:, 'w_act'] = self.test_data[cfg.resp_nme] * \
                self.test_data[cfg.weight_nme]
        if cfg.binary_resp_nme:
            self.train_data.loc[:, 'w_binary_act'] = self.train_data[cfg.binary_resp_nme] * \
                self.train_data[cfg.weight_nme]
            if test_has_binary:
                self.test_data.loc[:, 'w_binary_act'] = self.test_data[cfg.binary_resp_nme] * \
                    self.test_data[cfg.weight_nme]
        # High-quantile clipping absorbs outliers; removing it lets extremes dominate loss.
        q99 = self.train_data[cfg.resp_nme].quantile(0.999)
        self.train_data[cfg.resp_nme] = self.train_data[cfg.resp_nme].clip(
            upper=q99)
        cate_list = list(cfg.cate_list or [])
        if cate_list:
            for cate in cate_list:
                self.train_data[cate] = self.train_data[cate].astype(
                    'category')
                self.test_data[cate] = self.test_data[cate].astype('category')
                cats = self.train_data[cate].cat.categories
                self.cat_categories_for_shap[cate] = list(cats)
        self.num_features = [
            nme for nme in cfg.factor_nmes if nme not in cate_list]
        train_oht = self.train_data[cfg.factor_nmes +
                                    [cfg.weight_nme] + [cfg.resp_nme]].copy()
        test_oht = self.test_data[cfg.factor_nmes +
                                  [cfg.weight_nme] + [cfg.resp_nme]].copy()
        train_oht = pd.get_dummies(
            train_oht,
            columns=cate_list,
            drop_first=True,
            dtype=np.int8
        )
        test_oht = pd.get_dummies(
            test_oht,
            columns=cate_list,
            drop_first=True,
            dtype=np.int8
        )

        # Fill missing dummy columns when reindexing to align train/test columns.
        test_oht = test_oht.reindex(columns=train_oht.columns, fill_value=0)

        # Keep unscaled one-hot data for fold-specific scaling to avoid leakage.
        self.train_oht_data = train_oht.copy(deep=True)
        self.test_oht_data = test_oht.copy(deep=True)

        train_oht_scaled = train_oht.copy(deep=True)
        test_oht_scaled = test_oht.copy(deep=True)
        for num_chr in self.num_features:
            # Scale per column so features are on comparable ranges for NN stability.
            scaler = StandardScaler()
            train_oht_scaled[num_chr] = scaler.fit_transform(
                train_oht_scaled[num_chr].values.reshape(-1, 1))
            test_oht_scaled[num_chr] = scaler.transform(
                test_oht_scaled[num_chr].values.reshape(-1, 1))
        # Fill missing dummy columns when reindexing to align train/test columns.
        test_oht_scaled = test_oht_scaled.reindex(
            columns=train_oht_scaled.columns, fill_value=0)
        self.train_oht_scl_data = train_oht_scaled
        self.test_oht_scl_data = test_oht_scaled
        excluded = {cfg.weight_nme, cfg.resp_nme}
        self.var_nmes = [
            col for col in train_oht_scaled.columns if col not in excluded
        ]
        return self
