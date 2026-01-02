from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import os
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import statsmodels.api as sm
from sklearn.model_selection import ShuffleSplit
from sklearn.preprocessing import StandardScaler

from .config_preprocess import BayesOptConfig, DatasetPreprocessor, OutputManager, VersionManager
from .models import GraphNeuralNetSklearn
from .trainers import FTTrainer, GLMTrainer, GNNTrainer, ResNetTrainer, XGBTrainer
from .utils import EPS, PlotUtils, infer_factor_and_cate_list, set_global_seed
try:
    from ..plotting import curves as plot_curves
    from ..plotting import diagnostics as plot_diagnostics
    from ..plotting.common import PlotStyle, finalize_figure
    from ..explain import gradients as explain_gradients
    from ..explain import permutation as explain_permutation
    from ..explain import shap_utils as explain_shap
except Exception:  # pragma: no cover - optional for legacy imports
    try:  # best-effort for non-package imports
        from ins_pricing.plotting import curves as plot_curves
        from ins_pricing.plotting import diagnostics as plot_diagnostics
        from ins_pricing.plotting.common import PlotStyle, finalize_figure
        from ins_pricing.explain import gradients as explain_gradients
        from ins_pricing.explain import permutation as explain_permutation
        from ins_pricing.explain import shap_utils as explain_shap
    except Exception:  # pragma: no cover
        plot_curves = None
        plot_diagnostics = None
        PlotStyle = None
        finalize_figure = None
        explain_gradients = None
        explain_permutation = None
        explain_shap = None

# BayesOpt orchestration and SHAP utilities
# =============================================================================
class BayesOptModel:
    def __init__(self, train_data, test_data,
                 model_nme, resp_nme, weight_nme, factor_nmes: Optional[List[str]] = None, task_type='regression',
                 binary_resp_nme=None,
                 cate_list=None, prop_test=0.25, rand_seed=None,
                 epochs=100, use_gpu=True,
                 use_resn_data_parallel: bool = False, use_ft_data_parallel: bool = False,
                 use_gnn_data_parallel: bool = False,
                 use_resn_ddp: bool = False, use_ft_ddp: bool = False,
                 use_gnn_ddp: bool = False,
                 output_dir: Optional[str] = None,
                 gnn_use_approx_knn: bool = True,
                 gnn_approx_knn_threshold: int = 50000,
                 gnn_graph_cache: Optional[str] = None,
                 gnn_max_gpu_knn_nodes: Optional[int] = 200000,
                 gnn_knn_gpu_mem_ratio: float = 0.9,
                 gnn_knn_gpu_mem_overhead: float = 2.0,
                 ft_role: str = "model",
                 ft_feature_prefix: str = "ft_emb",
                 ft_num_numeric_tokens: Optional[int] = None,
                 infer_categorical_max_unique: int = 50,
                 infer_categorical_max_ratio: float = 0.05,
                 reuse_best_params: bool = False,
                 xgb_max_depth_max: int = 25,
                 xgb_n_estimators_max: int = 500,
                 resn_weight_decay: Optional[float] = None,
                 final_ensemble: bool = False,
                 final_ensemble_k: int = 3,
                 final_refit: bool = True,
                 optuna_storage: Optional[str] = None,
                 optuna_study_prefix: Optional[str] = None,
                 best_params_files: Optional[Dict[str, str]] = None):
        """Orchestrate BayesOpt training across multiple trainers.

        Args:
            train_data: Training DataFrame.
            test_data: Test DataFrame.
            model_nme: Model name prefix used in outputs.
            resp_nme: Target column name.
            weight_nme: Sample weight column name.
            factor_nmes: Feature column list.
            task_type: "regression" or "classification".
            binary_resp_nme: Optional binary target for lift curves.
            cate_list: Categorical feature list.
            prop_test: Validation split ratio in CV.
            rand_seed: Random seed.
            epochs: NN training epochs.
            use_gpu: Prefer GPU when available.
            use_resn_data_parallel: Enable DataParallel for ResNet.
            use_ft_data_parallel: Enable DataParallel for FTTransformer.
            use_gnn_data_parallel: Enable DataParallel for GNN.
            use_resn_ddp: Enable DDP for ResNet.
            use_ft_ddp: Enable DDP for FTTransformer.
            use_gnn_ddp: Enable DDP for GNN.
            output_dir: Output root for models/results/plots.
            gnn_use_approx_knn: Use approximate kNN when available.
            gnn_approx_knn_threshold: Row threshold to switch to approximate kNN.
            gnn_graph_cache: Optional adjacency cache path.
            gnn_max_gpu_knn_nodes: Force CPU kNN above this node count to avoid OOM.
            gnn_knn_gpu_mem_ratio: Fraction of free GPU memory for kNN.
            gnn_knn_gpu_mem_overhead: Temporary memory multiplier for GPU kNN.
            ft_num_numeric_tokens: Number of numeric tokens for FT (None = auto).
            final_ensemble: Enable k-fold model averaging at the final stage.
            final_ensemble_k: Number of folds for averaging.
            final_refit: Refit on full data using best stopping point.
        """
        inferred_factors, inferred_cats = infer_factor_and_cate_list(
            train_df=train_data,
            test_df=test_data,
            resp_nme=resp_nme,
            weight_nme=weight_nme,
            binary_resp_nme=binary_resp_nme,
            factor_nmes=factor_nmes,
            cate_list=cate_list,
            infer_categorical_max_unique=int(infer_categorical_max_unique),
            infer_categorical_max_ratio=float(infer_categorical_max_ratio),
        )

        cfg = BayesOptConfig(
            model_nme=model_nme,
            task_type=task_type,
            resp_nme=resp_nme,
            weight_nme=weight_nme,
            factor_nmes=list(inferred_factors),
            binary_resp_nme=binary_resp_nme,
            cate_list=list(inferred_cats) if inferred_cats else None,
            prop_test=prop_test,
            rand_seed=rand_seed,
            epochs=epochs,
            use_gpu=use_gpu,
            xgb_max_depth_max=int(xgb_max_depth_max),
            xgb_n_estimators_max=int(xgb_n_estimators_max),
            use_resn_data_parallel=use_resn_data_parallel,
            use_ft_data_parallel=use_ft_data_parallel,
            use_resn_ddp=use_resn_ddp,
            use_gnn_data_parallel=use_gnn_data_parallel,
            use_ft_ddp=use_ft_ddp,
            use_gnn_ddp=use_gnn_ddp,
            gnn_use_approx_knn=gnn_use_approx_knn,
            gnn_approx_knn_threshold=gnn_approx_knn_threshold,
            gnn_graph_cache=gnn_graph_cache,
            gnn_max_gpu_knn_nodes=gnn_max_gpu_knn_nodes,
            gnn_knn_gpu_mem_ratio=gnn_knn_gpu_mem_ratio,
            gnn_knn_gpu_mem_overhead=gnn_knn_gpu_mem_overhead,
            output_dir=output_dir,
            optuna_storage=optuna_storage,
            optuna_study_prefix=optuna_study_prefix,
            best_params_files=best_params_files,
            ft_role=str(ft_role or "model"),
            ft_feature_prefix=str(ft_feature_prefix or "ft_emb"),
            ft_num_numeric_tokens=ft_num_numeric_tokens,
            reuse_best_params=bool(reuse_best_params),
            resn_weight_decay=float(resn_weight_decay)
            if resn_weight_decay is not None
            else 1e-4,
            final_ensemble=bool(final_ensemble),
            final_ensemble_k=int(final_ensemble_k),
            final_refit=bool(final_refit),
        )
        self.config = cfg
        self.model_nme = cfg.model_nme
        self.task_type = cfg.task_type
        self.resp_nme = cfg.resp_nme
        self.weight_nme = cfg.weight_nme
        self.factor_nmes = cfg.factor_nmes
        self.binary_resp_nme = cfg.binary_resp_nme
        self.cate_list = list(cfg.cate_list or [])
        self.prop_test = cfg.prop_test
        self.epochs = cfg.epochs
        self.rand_seed = cfg.rand_seed if cfg.rand_seed is not None else np.random.randint(
            1, 10000)
        set_global_seed(int(self.rand_seed))
        self.use_gpu = bool(cfg.use_gpu and torch.cuda.is_available())
        self.output_manager = OutputManager(
            cfg.output_dir or os.getcwd(), self.model_nme)

        preprocessor = DatasetPreprocessor(train_data, test_data, cfg).run()
        self.train_data = preprocessor.train_data
        self.test_data = preprocessor.test_data
        self.train_oht_data = preprocessor.train_oht_data
        self.test_oht_data = preprocessor.test_oht_data
        self.train_oht_scl_data = preprocessor.train_oht_scl_data
        self.test_oht_scl_data = preprocessor.test_oht_scl_data
        self.var_nmes = preprocessor.var_nmes
        self.num_features = preprocessor.num_features
        self.cat_categories_for_shap = preprocessor.cat_categories_for_shap
        self.geo_token_cols: List[str] = []
        self.train_geo_tokens: Optional[pd.DataFrame] = None
        self.test_geo_tokens: Optional[pd.DataFrame] = None
        self.geo_gnn_model: Optional[GraphNeuralNetSklearn] = None
        self._add_region_effect()

        self.cv = ShuffleSplit(n_splits=int(1/self.prop_test),
                               test_size=self.prop_test,
                               random_state=self.rand_seed)
        if self.task_type == 'classification':
            self.obj = 'binary:logistic'
        else:  # regression task
            if 'f' in self.model_nme:
                self.obj = 'count:poisson'
            elif 's' in self.model_nme:
                self.obj = 'reg:gamma'
            elif 'bc' in self.model_nme:
                self.obj = 'reg:tweedie'
            else:
                self.obj = 'reg:tweedie'
        self.fit_params = {
            'sample_weight': self.train_data[self.weight_nme].values
        }
        self.model_label: List[str] = []
        self.optuna_storage = cfg.optuna_storage
        self.optuna_study_prefix = cfg.optuna_study_prefix or "bayesopt"

        # Keep trainers in a dict for unified access and easy extension.
        self.trainers: Dict[str, TrainerBase] = {
            'glm': GLMTrainer(self),
            'xgb': XGBTrainer(self),
            'resn': ResNetTrainer(self),
            'ft': FTTrainer(self),
            'gnn': GNNTrainer(self),
        }
        self._prepare_geo_tokens()
        self.xgb_best = None
        self.resn_best = None
        self.gnn_best = None
        self.glm_best = None
        self.ft_best = None
        self.best_xgb_params = None
        self.best_resn_params = None
        self.best_gnn_params = None
        self.best_ft_params = None
        self.best_xgb_trial = None
        self.best_resn_trial = None
        self.best_gnn_trial = None
        self.best_ft_trial = None
        self.best_glm_params = None
        self.best_glm_trial = None
        self.xgb_load = None
        self.resn_load = None
        self.gnn_load = None
        self.ft_load = None
        self.version_manager = VersionManager(self.output_manager)

    def default_tweedie_power(self, obj: Optional[str] = None) -> Optional[float]:
        if self.task_type == 'classification':
            return None
        objective = obj or getattr(self, "obj", None)
        if objective == 'count:poisson':
            return 1.0
        if objective == 'reg:gamma':
            return 2.0
        return 1.5

    def _build_geo_tokens(self, params_override: Optional[Dict[str, Any]] = None):
        """Internal builder; allows trial overrides and returns None on failure."""
        geo_cols = list(self.config.geo_feature_nmes or [])
        if not geo_cols:
            return None

        available = [c for c in geo_cols if c in self.train_data.columns]
        if not available:
            return None

        # Preprocess text/numeric: fill numeric with median, label-encode text, map unknowns.
        proc_train = {}
        proc_test = {}
        for col in available:
            s_train = self.train_data[col]
            s_test = self.test_data[col]
            if pd.api.types.is_numeric_dtype(s_train):
                tr = pd.to_numeric(s_train, errors="coerce")
                te = pd.to_numeric(s_test, errors="coerce")
                med = np.nanmedian(tr)
                proc_train[col] = np.nan_to_num(tr, nan=med).astype(np.float32)
                proc_test[col] = np.nan_to_num(te, nan=med).astype(np.float32)
            else:
                cats = pd.Categorical(s_train.astype(str))
                tr_codes = cats.codes.astype(np.float32, copy=True)
                tr_codes[tr_codes < 0] = len(cats.categories)
                te_cats = pd.Categorical(
                    s_test.astype(str), categories=cats.categories)
                te_codes = te_cats.codes.astype(np.float32, copy=True)
                te_codes[te_codes < 0] = len(cats.categories)
                proc_train[col] = tr_codes
                proc_test[col] = te_codes

        train_geo_raw = pd.DataFrame(proc_train, index=self.train_data.index)
        test_geo_raw = pd.DataFrame(proc_test, index=self.test_data.index)

        scaler = StandardScaler()
        train_geo = pd.DataFrame(
            scaler.fit_transform(train_geo_raw),
            columns=available,
            index=self.train_data.index
        )
        test_geo = pd.DataFrame(
            scaler.transform(test_geo_raw),
            columns=available,
            index=self.test_data.index
        )

        tw_power = self.default_tweedie_power()

        cfg = params_override or {}
        try:
            geo_gnn = GraphNeuralNetSklearn(
                model_nme=f"{self.model_nme}_geo",
                input_dim=len(available),
                hidden_dim=cfg.get("geo_token_hidden_dim",
                                   self.config.geo_token_hidden_dim),
                num_layers=cfg.get("geo_token_layers",
                                   self.config.geo_token_layers),
                k_neighbors=cfg.get("geo_token_k_neighbors",
                                    self.config.geo_token_k_neighbors),
                dropout=cfg.get("geo_token_dropout",
                                self.config.geo_token_dropout),
                learning_rate=cfg.get(
                    "geo_token_learning_rate", self.config.geo_token_learning_rate),
                epochs=int(cfg.get("geo_token_epochs",
                           self.config.geo_token_epochs)),
                patience=5,
                task_type=self.task_type,
                tweedie_power=tw_power,
                use_data_parallel=False,
                use_ddp=False,
                use_approx_knn=self.config.gnn_use_approx_knn,
                approx_knn_threshold=self.config.gnn_approx_knn_threshold,
                graph_cache_path=None,
                max_gpu_knn_nodes=self.config.gnn_max_gpu_knn_nodes,
                knn_gpu_mem_ratio=self.config.gnn_knn_gpu_mem_ratio,
                knn_gpu_mem_overhead=self.config.gnn_knn_gpu_mem_overhead
            )
            geo_gnn.fit(
                train_geo,
                self.train_data[self.resp_nme],
                self.train_data[self.weight_nme]
            )
            train_embed = geo_gnn.encode(train_geo)
            test_embed = geo_gnn.encode(test_geo)
            cols = [f"geo_token_{i}" for i in range(train_embed.shape[1])]
            train_tokens = pd.DataFrame(
                train_embed, index=self.train_data.index, columns=cols)
            test_tokens = pd.DataFrame(
                test_embed, index=self.test_data.index, columns=cols)
            return train_tokens, test_tokens, cols, geo_gnn
        except Exception as exc:
            print(f"[GeoToken] Generation failed: {exc}")
            return None

    def _prepare_geo_tokens(self) -> None:
        """Build and persist geo tokens with default config values."""
        gnn_trainer = self.trainers.get("gnn")
        if gnn_trainer is not None and hasattr(gnn_trainer, "prepare_geo_tokens"):
            try:
                gnn_trainer.prepare_geo_tokens(force=False)  # type: ignore[attr-defined]
                return
            except Exception as exc:
                print(f"[GeoToken] GNNTrainer generation failed: {exc}")

        result = self._build_geo_tokens()
        if result is None:
            return
        train_tokens, test_tokens, cols, geo_gnn = result
        self.train_geo_tokens = train_tokens
        self.test_geo_tokens = test_tokens
        self.geo_token_cols = cols
        self.geo_gnn_model = geo_gnn
        print(f"[GeoToken] Generated {len(cols)}-dim geo tokens; injecting into FT.")

    def _add_region_effect(self) -> None:
        """Partial pooling over province/city to create a smoothed region_effect feature."""
        prov_col = self.config.region_province_col
        city_col = self.config.region_city_col
        if not prov_col or not city_col:
            return
        for col in [prov_col, city_col]:
            if col not in self.train_data.columns:
                print(f"[RegionEffect] Missing column {col}; skipped.")
                return

        def safe_mean(df: pd.DataFrame) -> float:
            w = df[self.weight_nme]
            y = df[self.resp_nme]
            denom = max(float(w.sum()), EPS)
            return float((y * w).sum() / denom)

        global_mean = safe_mean(self.train_data)
        alpha = max(float(self.config.region_effect_alpha), 0.0)

        w_all = self.train_data[self.weight_nme]
        y_all = self.train_data[self.resp_nme]
        yw_all = y_all * w_all

        prov_sumw = w_all.groupby(self.train_data[prov_col]).sum()
        prov_sumyw = yw_all.groupby(self.train_data[prov_col]).sum()
        prov_mean = (prov_sumyw / prov_sumw.clip(lower=EPS)).astype(float)
        prov_mean = prov_mean.fillna(global_mean)

        city_sumw = self.train_data.groupby([prov_col, city_col])[
            self.weight_nme].sum()
        city_sumyw = yw_all.groupby(
            [self.train_data[prov_col], self.train_data[city_col]]).sum()
        city_df = pd.DataFrame({
            "sum_w": city_sumw,
            "sum_yw": city_sumyw,
        })
        city_df["prior"] = city_df.index.get_level_values(0).map(
            prov_mean).fillna(global_mean)
        city_df["effect"] = (
            city_df["sum_yw"] + alpha * city_df["prior"]
        ) / (city_df["sum_w"] + alpha).clip(lower=EPS)
        city_effect = city_df["effect"]

        def lookup_effect(df: pd.DataFrame) -> pd.Series:
            idx = pd.MultiIndex.from_frame(df[[prov_col, city_col]])
            effects = city_effect.reindex(idx).to_numpy(dtype=np.float64)
            prov_fallback = df[prov_col].map(
                prov_mean).fillna(global_mean).to_numpy(dtype=np.float64)
            effects = np.where(np.isfinite(effects), effects, prov_fallback)
            effects = np.where(np.isfinite(effects), effects, global_mean)
            return pd.Series(effects, index=df.index, dtype=np.float32)

        re_train = lookup_effect(self.train_data)
        re_test = lookup_effect(self.test_data)

        col_name = "region_effect"
        self.train_data[col_name] = re_train
        self.test_data[col_name] = re_test

        # Sync into one-hot and scaled variants.
        for df in [self.train_oht_data, self.test_oht_data]:
            if df is not None:
                df[col_name] = re_train if df is self.train_oht_data else re_test

        # Standardize region_effect and propagate.
        scaler = StandardScaler()
        re_train_s = scaler.fit_transform(
            re_train.values.reshape(-1, 1)).astype(np.float32).reshape(-1)
        re_test_s = scaler.transform(
            re_test.values.reshape(-1, 1)).astype(np.float32).reshape(-1)
        for df in [self.train_oht_scl_data, self.test_oht_scl_data]:
            if df is not None:
                df[col_name] = re_train_s if df is self.train_oht_scl_data else re_test_s

        # Update feature lists.
        if col_name not in self.factor_nmes:
            self.factor_nmes.append(col_name)
        if col_name not in self.num_features:
            self.num_features.append(col_name)
        if self.train_oht_scl_data is not None:
            excluded = {self.weight_nme, self.resp_nme}
            self.var_nmes = [
                col for col in self.train_oht_scl_data.columns if col not in excluded
            ]

    # Single-factor plotting helper.
    def plot_oneway(self, n_bins=10):
        if plot_diagnostics is None:
            for c in self.factor_nmes:
                fig = plt.figure(figsize=(7, 5))
                if c in self.cate_list:
                    group_col = c
                    plot_source = self.train_data
                else:
                    group_col = f'{c}_bins'
                    bins = pd.qcut(
                        self.train_data[c],
                        n_bins,
                        duplicates='drop'  # Drop duplicate quantiles to avoid errors.
                    )
                    plot_source = self.train_data.assign(**{group_col: bins})
                plot_data = plot_source.groupby(
                    [group_col], observed=True).sum(numeric_only=True)
                plot_data.reset_index(inplace=True)
                plot_data['act_v'] = plot_data['w_act'] / \
                    plot_data[self.weight_nme]
                ax = fig.add_subplot(111)
                ax.plot(plot_data.index, plot_data['act_v'],
                        label='Actual', color='red')
                ax.set_title(
                    'Analysis of  %s : Train Data' % group_col,
                    fontsize=8)
                plt.xticks(plot_data.index,
                           list(plot_data[group_col].astype(str)),
                           rotation=90)
                if len(list(plot_data[group_col].astype(str))) > 50:
                    plt.xticks(fontsize=3)
                else:
                    plt.xticks(fontsize=6)
                plt.yticks(fontsize=6)
                ax2 = ax.twinx()
                ax2.bar(plot_data.index,
                        plot_data[self.weight_nme],
                        alpha=0.5, color='seagreen')
                plt.yticks(fontsize=6)
                plt.margins(0.05)
                plt.subplots_adjust(wspace=0.3)
                save_path = self.output_manager.plot_path(
                    f'00_{self.model_nme}_{group_col}_oneway.png')
                plt.savefig(save_path, dpi=300)
                plt.close(fig)
            return

        if "w_act" not in self.train_data.columns:
            print("[Oneway] Missing w_act column; skip plotting.", flush=True)
            return

        for c in self.factor_nmes:
            is_cat = c in (self.cate_list or [])
            group_col = c if is_cat else f"{c}_bins"
            title = f"Analysis of {group_col} : Train Data"
            save_path = self.output_manager.plot_path(
                f"00_{self.model_nme}_{group_col}_oneway.png"
            )
            plot_diagnostics.plot_oneway(
                self.train_data,
                feature=c,
                weight_col=self.weight_nme,
                target_col="w_act",
                n_bins=n_bins,
                is_categorical=is_cat,
                title=title,
                save_path=save_path,
                show=False,
            )

    def _require_trainer(self, model_key: str) -> "TrainerBase":
        trainer = self.trainers.get(model_key)
        if trainer is None:
            raise KeyError(f"Unknown model key: {model_key}")
        return trainer

    def _pred_vector_columns(self, pred_prefix: str) -> List[str]:
        """Return vector feature columns like pred_<prefix>_0.. sorted by suffix."""
        col_prefix = f"pred_{pred_prefix}_"
        cols = [c for c in self.train_data.columns if c.startswith(col_prefix)]

        def sort_key(name: str):
            tail = name.rsplit("_", 1)[-1]
            try:
                return (0, int(tail))
            except Exception:
                return (1, tail)

        cols.sort(key=sort_key)
        return cols

    def _inject_pred_features(self, pred_prefix: str) -> List[str]:
        """Inject pred_<prefix> or pred_<prefix>_i columns into features and return names."""
        cols = self._pred_vector_columns(pred_prefix)
        if cols:
            self.add_numeric_features_from_columns(cols)
            return cols
        scalar_col = f"pred_{pred_prefix}"
        if scalar_col in self.train_data.columns:
            self.add_numeric_feature_from_column(scalar_col)
            return [scalar_col]
        return []

    def _maybe_load_best_params(self, model_key: str, trainer: "TrainerBase") -> None:
        # 1) If best_params_files is specified, load and skip tuning.
        best_params_files = getattr(self.config, "best_params_files", None) or {}
        best_params_file = best_params_files.get(model_key)
        if best_params_file and not trainer.best_params:
            trainer.best_params = IOUtils.load_params_file(best_params_file)
            trainer.best_trial = None
            print(
                f"[Optuna][{trainer.label}] Loaded best_params from {best_params_file}; skip tuning."
            )

        # 2) If reuse_best_params is enabled, prefer version snapshots; else load legacy CSV.
        reuse_params = bool(getattr(self.config, "reuse_best_params", False))
        if reuse_params and not trainer.best_params:
            payload = self.version_manager.load_latest(f"{model_key}_best")
            best_params = None if payload is None else payload.get("best_params")
            if best_params:
                trainer.best_params = best_params
                trainer.best_trial = None
                trainer.study_name = payload.get(
                    "study_name") if isinstance(payload, dict) else None
                print(
                    f"[Optuna][{trainer.label}] Reusing best_params from versions snapshot.")
                return

            params_path = self.output_manager.result_path(
                f'{self.model_nme}_bestparams_{trainer.label.lower()}.csv'
            )
            if os.path.exists(params_path):
                try:
                    trainer.best_params = IOUtils.load_params_file(params_path)
                    trainer.best_trial = None
                    print(
                        f"[Optuna][{trainer.label}] Reusing best_params from {params_path}.")
                except ValueError:
                    # Legacy compatibility: ignore empty files and continue tuning.
                    pass

    # Generic optimization entry point.
    def optimize_model(self, model_key: str, max_evals: int = 100):
        if model_key not in self.trainers:
            print(f"Warning: Unknown model key: {model_key}")
            return

        trainer = self._require_trainer(model_key)
        self._maybe_load_best_params(model_key, trainer)

        should_tune = not trainer.best_params
        if should_tune:
            if model_key == "ft" and str(self.config.ft_role) == "unsupervised_embedding":
                if hasattr(trainer, "cross_val_unsupervised"):
                    trainer.tune(
                        max_evals,
                        objective_fn=getattr(trainer, "cross_val_unsupervised")
                    )
                else:
                    raise RuntimeError(
                        "FT trainer does not support unsupervised Optuna objective.")
            else:
                trainer.tune(max_evals)

        if model_key == "ft" and str(self.config.ft_role) != "model":
            prefix = str(self.config.ft_feature_prefix or "ft_emb")
            role = str(self.config.ft_role)
            if role == "embedding":
                trainer.train_as_feature(
                    pred_prefix=prefix, feature_mode="embedding")
            elif role == "unsupervised_embedding":
                trainer.pretrain_unsupervised_as_feature(
                    pred_prefix=prefix,
                    params=trainer.best_params
                )
            else:
                raise ValueError(
                    f"Unsupported ft_role='{role}', expected 'model'/'embedding'/'unsupervised_embedding'.")

            # Inject generated prediction/embedding columns as features (scalar or vector).
            self._inject_pred_features(prefix)
            # Do not add FT as a standalone model label; downstream models handle evaluation.
        else:
            trainer.train()

        if bool(getattr(self.config, "final_ensemble", False)):
            k = int(getattr(self.config, "final_ensemble_k", 3) or 3)
            if k > 1:
                if model_key == "ft" and str(self.config.ft_role) != "model":
                    pass
                elif hasattr(trainer, "ensemble_predict"):
                    trainer.ensemble_predict(k)
                else:
                    print(
                        f"[Ensemble] Trainer '{model_key}' does not support ensemble prediction.",
                        flush=True,
                    )

        # Update context fields for backward compatibility.
        setattr(self, f"{model_key}_best", trainer.model)
        setattr(self, f"best_{model_key}_params", trainer.best_params)
        setattr(self, f"best_{model_key}_trial", trainer.best_trial)
        # Save a snapshot for traceability.
        study_name = getattr(trainer, "study_name", None)
        if study_name is None and trainer.best_trial is not None:
            study_obj = getattr(trainer.best_trial, "study", None)
            study_name = getattr(study_obj, "study_name", None)
        snapshot = {
            "model_key": model_key,
            "timestamp": datetime.now().isoformat(),
            "best_params": trainer.best_params,
            "study_name": study_name,
            "config": asdict(self.config),
        }
        self.version_manager.save(f"{model_key}_best", snapshot)

    def add_numeric_feature_from_column(self, col_name: str) -> None:
        """Add an existing column as a feature and sync one-hot/scaled tables."""
        if col_name not in self.train_data.columns or col_name not in self.test_data.columns:
            raise KeyError(
                f"Column '{col_name}' must exist in both train_data and test_data.")

        if col_name not in self.factor_nmes:
            self.factor_nmes.append(col_name)
        if col_name not in self.config.factor_nmes:
            self.config.factor_nmes.append(col_name)

        if col_name not in self.cate_list and col_name not in self.num_features:
            self.num_features.append(col_name)

        if self.train_oht_data is not None and self.test_oht_data is not None:
            self.train_oht_data[col_name] = self.train_data[col_name].values
            self.test_oht_data[col_name] = self.test_data[col_name].values
        if self.train_oht_scl_data is not None and self.test_oht_scl_data is not None:
            scaler = StandardScaler()
            tr = self.train_data[col_name].to_numpy(
                dtype=np.float32, copy=False).reshape(-1, 1)
            te = self.test_data[col_name].to_numpy(
                dtype=np.float32, copy=False).reshape(-1, 1)
            self.train_oht_scl_data[col_name] = scaler.fit_transform(
                tr).reshape(-1)
            self.test_oht_scl_data[col_name] = scaler.transform(te).reshape(-1)

        if col_name not in self.var_nmes:
            self.var_nmes.append(col_name)

    def add_numeric_features_from_columns(self, col_names: List[str]) -> None:
        if not col_names:
            return

        missing = [
            col for col in col_names
            if col not in self.train_data.columns or col not in self.test_data.columns
        ]
        if missing:
            raise KeyError(
                f"Column(s) {missing} must exist in both train_data and test_data."
            )

        for col_name in col_names:
            if col_name not in self.factor_nmes:
                self.factor_nmes.append(col_name)
            if col_name not in self.config.factor_nmes:
                self.config.factor_nmes.append(col_name)
            if col_name not in self.cate_list and col_name not in self.num_features:
                self.num_features.append(col_name)
            if col_name not in self.var_nmes:
                self.var_nmes.append(col_name)

        if self.train_oht_data is not None and self.test_oht_data is not None:
            self.train_oht_data.loc[:, col_names] = self.train_data[col_names].to_numpy(copy=False)
            self.test_oht_data.loc[:, col_names] = self.test_data[col_names].to_numpy(copy=False)

        if self.train_oht_scl_data is not None and self.test_oht_scl_data is not None:
            scaler = StandardScaler()
            tr = self.train_data[col_names].to_numpy(dtype=np.float32, copy=False)
            te = self.test_data[col_names].to_numpy(dtype=np.float32, copy=False)
            self.train_oht_scl_data.loc[:, col_names] = scaler.fit_transform(tr)
            self.test_oht_scl_data.loc[:, col_names] = scaler.transform(te)

    def prepare_ft_as_feature(self, max_evals: int = 50, pred_prefix: str = "ft_feat") -> str:
        """Train FT as a feature generator and return the downstream column name."""
        ft_trainer = self._require_trainer("ft")
        ft_trainer.tune(max_evals=max_evals)
        if hasattr(ft_trainer, "train_as_feature"):
            ft_trainer.train_as_feature(pred_prefix=pred_prefix)
        else:
            ft_trainer.train()
        feature_col = f"pred_{pred_prefix}"
        self.add_numeric_feature_from_column(feature_col)
        return feature_col

    def prepare_ft_embedding_as_features(self, max_evals: int = 50, pred_prefix: str = "ft_emb") -> List[str]:
        """Train FT and inject pooled embeddings as vector features pred_<prefix>_0.. ."""
        ft_trainer = self._require_trainer("ft")
        ft_trainer.tune(max_evals=max_evals)
        if hasattr(ft_trainer, "train_as_feature"):
            ft_trainer.train_as_feature(
                pred_prefix=pred_prefix, feature_mode="embedding")
        else:
            raise RuntimeError(
                "FT trainer does not support embedding feature mode.")
        cols = self._pred_vector_columns(pred_prefix)
        if not cols:
            raise RuntimeError(
                f"No embedding columns were generated for prefix '{pred_prefix}'.")
        self.add_numeric_features_from_columns(cols)
        return cols

    def prepare_ft_unsupervised_embedding_as_features(self,
                                                      pred_prefix: str = "ft_uemb",
                                                      params: Optional[Dict[str,
                                                                            Any]] = None,
                                                      mask_prob_num: float = 0.15,
                                                      mask_prob_cat: float = 0.15,
                                                      num_loss_weight: float = 1.0,
                                                      cat_loss_weight: float = 1.0) -> List[str]:
        """Export embeddings after FT self-supervised masked reconstruction pretraining."""
        ft_trainer = self._require_trainer("ft")
        if not hasattr(ft_trainer, "pretrain_unsupervised_as_feature"):
            raise RuntimeError(
                "FT trainer does not support unsupervised pretraining.")
        ft_trainer.pretrain_unsupervised_as_feature(
            pred_prefix=pred_prefix,
            params=params,
            mask_prob_num=mask_prob_num,
            mask_prob_cat=mask_prob_cat,
            num_loss_weight=num_loss_weight,
            cat_loss_weight=cat_loss_weight
        )
        cols = self._pred_vector_columns(pred_prefix)
        if not cols:
            raise RuntimeError(
                f"No embedding columns were generated for prefix '{pred_prefix}'.")
        self.add_numeric_features_from_columns(cols)
        return cols

    # GLM Bayesian optimization wrapper.
    def bayesopt_glm(self, max_evals=50):
        self.optimize_model('glm', max_evals)

    # XGBoost Bayesian optimization wrapper.
    def bayesopt_xgb(self, max_evals=100):
        self.optimize_model('xgb', max_evals)

    # ResNet Bayesian optimization wrapper.
    def bayesopt_resnet(self, max_evals=100):
        self.optimize_model('resn', max_evals)

    # GNN Bayesian optimization wrapper.
    def bayesopt_gnn(self, max_evals=50):
        self.optimize_model('gnn', max_evals)

    # FT-Transformer Bayesian optimization wrapper.
    def bayesopt_ft(self, max_evals=50):
        self.optimize_model('ft', max_evals)

    # Lift curve plotting.
    def plot_lift(self, model_label, pred_nme, n_bins=10):
        model_map = {
            'Xgboost': 'pred_xgb',
            'ResNet': 'pred_resn',
            'ResNetClassifier': 'pred_resn',
            'GLM': 'pred_glm',
            'GNN': 'pred_gnn',
        }
        if str(self.config.ft_role) == "model":
            model_map.update({
                'FTTransformer': 'pred_ft',
                'FTTransformerClassifier': 'pred_ft',
            })
        for k, v in model_map.items():
            if model_label.startswith(k):
                pred_nme = v
                break

        datasets = []
        for title, data in [
            ('Lift Chart on Train Data', self.train_data),
            ('Lift Chart on Test Data', self.test_data),
        ]:
            if 'w_act' not in data.columns or data['w_act'].isna().all():
                print(
                    f"[Lift] Missing labels for {title}; skip.",
                    flush=True,
                )
                continue
            datasets.append((title, data))

        if not datasets:
            print("[Lift] No labeled data available; skip plotting.", flush=True)
            return

        if plot_curves is None:
            fig = plt.figure(figsize=(11, 5))
            positions = [111] if len(datasets) == 1 else [121, 122]
            for pos, (title, data) in zip(positions, datasets):
                if pred_nme not in data.columns or f'w_{pred_nme}' not in data.columns:
                    print(
                        f"[Lift] Missing prediction columns in {title}; skip.",
                        flush=True,
                    )
                    continue
                lift_df = pd.DataFrame({
                    'pred': data[pred_nme].values,
                    'w_pred': data[f'w_{pred_nme}'].values,
                    'act': data['w_act'].values,
                    'weight': data[self.weight_nme].values
                })
                plot_data = PlotUtils.split_data(lift_df, 'pred', 'weight', n_bins)
                denom = np.maximum(plot_data['weight'], EPS)
                plot_data['exp_v'] = plot_data['w_pred'] / denom
                plot_data['act_v'] = plot_data['act'] / denom
                plot_data = plot_data.reset_index()

                ax = fig.add_subplot(pos)
                PlotUtils.plot_lift_ax(ax, plot_data, title)

            plt.subplots_adjust(wspace=0.3)
            save_path = self.output_manager.plot_path(
                f'01_{self.model_nme}_{model_label}_lift.png')
            plt.savefig(save_path, dpi=300)
            plt.show()
            plt.close(fig)
            return

        style = PlotStyle() if PlotStyle else None
        fig, axes = plt.subplots(1, len(datasets), figsize=(11, 5))
        if len(datasets) == 1:
            axes = [axes]

        for ax, (title, data) in zip(axes, datasets):
            pred_vals = None
            if pred_nme in data.columns:
                pred_vals = data[pred_nme].values
            else:
                w_pred_col = f"w_{pred_nme}"
                if w_pred_col in data.columns:
                    denom = np.maximum(data[self.weight_nme].values, EPS)
                    pred_vals = data[w_pred_col].values / denom
            if pred_vals is None:
                print(
                    f"[Lift] Missing prediction columns in {title}; skip.",
                    flush=True,
                )
                continue

            plot_curves.plot_lift_curve(
                pred_vals,
                data['w_act'].values,
                data[self.weight_nme].values,
                n_bins=n_bins,
                title=title,
                pred_label="Predicted",
                act_label="Actual",
                weight_label="Earned Exposure",
                pred_weighted=False,
                actual_weighted=True,
                ax=ax,
                show=False,
                style=style,
            )

        plt.subplots_adjust(wspace=0.3)
        save_path = self.output_manager.plot_path(
            f'01_{self.model_nme}_{model_label}_lift.png')
        if finalize_figure:
            finalize_figure(fig, save_path=save_path, show=True, style=style)
        else:
            plt.savefig(save_path, dpi=300)
            plt.show()
            plt.close(fig)

    # Double lift curve plot.
    def plot_dlift(self, model_comp: List[str] = ['xgb', 'resn'], n_bins: int = 10) -> None:
        # Compare two models across bins.
        # Args:
        #   model_comp: model keys to compare (e.g., ['xgb', 'resn']).
        #   n_bins: number of bins for lift curves.
        if len(model_comp) != 2:
            raise ValueError("`model_comp` must contain two models to compare.")

        model_name_map = {
            'xgb': 'Xgboost',
            'resn': 'ResNet',
            'glm': 'GLM',
            'gnn': 'GNN',
        }
        if str(self.config.ft_role) == "model":
            model_name_map['ft'] = 'FTTransformer'

        name1, name2 = model_comp
        if name1 not in model_name_map or name2 not in model_name_map:
            raise ValueError(f"Unsupported model key. Choose from {list(model_name_map.keys())}.")

        datasets = []
        for data_name, data in [('Train Data', self.train_data),
                                ('Test Data', self.test_data)]:
            if 'w_act' not in data.columns or data['w_act'].isna().all():
                print(
                    f"[Double Lift] Missing labels for {data_name}; skip.",
                    flush=True,
                )
                continue
            datasets.append((data_name, data))

        if not datasets:
            print("[Double Lift] No labeled data available; skip plotting.", flush=True)
            return

        if plot_curves is None:
            fig, axes = plt.subplots(1, len(datasets), figsize=(11, 5))
            if len(datasets) == 1:
                axes = [axes]

            for ax, (data_name, data) in zip(axes, datasets):
                pred1_col = f'w_pred_{name1}'
                pred2_col = f'w_pred_{name2}'

                if pred1_col not in data.columns or pred2_col not in data.columns:
                    print(
                        f"Warning: missing prediction columns {pred1_col} or {pred2_col} in {data_name}. Skip plot.")
                    continue

                lift_data = pd.DataFrame({
                    'pred1': data[pred1_col].values,
                    'pred2': data[pred2_col].values,
                    'diff_ly': data[pred1_col].values / np.maximum(data[pred2_col].values, EPS),
                    'act': data['w_act'].values,
                    'weight': data[self.weight_nme].values
                })
                plot_data = PlotUtils.split_data(
                    lift_data, 'diff_ly', 'weight', n_bins)
                denom = np.maximum(plot_data['act'], EPS)
                plot_data['exp_v1'] = plot_data['pred1'] / denom
                plot_data['exp_v2'] = plot_data['pred2'] / denom
                plot_data['act_v'] = plot_data['act'] / denom
                plot_data.reset_index(inplace=True)

                label1 = model_name_map[name1]
                label2 = model_name_map[name2]

                PlotUtils.plot_dlift_ax(
                    ax, plot_data, f'Double Lift Chart on {data_name}', label1, label2)

            plt.subplots_adjust(bottom=0.25, top=0.95, right=0.8, wspace=0.3)
            save_path = self.output_manager.plot_path(
                f'02_{self.model_nme}_dlift_{name1}_vs_{name2}.png')
            plt.savefig(save_path, dpi=300)
            plt.show()
            plt.close(fig)
            return

        style = PlotStyle() if PlotStyle else None
        fig, axes = plt.subplots(1, len(datasets), figsize=(11, 5))
        if len(datasets) == 1:
            axes = [axes]

        label1 = model_name_map[name1]
        label2 = model_name_map[name2]

        for ax, (data_name, data) in zip(axes, datasets):
            weight_vals = data[self.weight_nme].values
            pred1 = None
            pred2 = None

            pred1_col = f"pred_{name1}"
            pred2_col = f"pred_{name2}"
            if pred1_col in data.columns:
                pred1 = data[pred1_col].values
            else:
                w_pred1_col = f"w_pred_{name1}"
                if w_pred1_col in data.columns:
                    pred1 = data[w_pred1_col].values / np.maximum(weight_vals, EPS)

            if pred2_col in data.columns:
                pred2 = data[pred2_col].values
            else:
                w_pred2_col = f"w_pred_{name2}"
                if w_pred2_col in data.columns:
                    pred2 = data[w_pred2_col].values / np.maximum(weight_vals, EPS)

            if pred1 is None or pred2 is None:
                print(
                    f"Warning: missing pred_{name1}/pred_{name2} or w_pred columns in {data_name}. Skip plot.")
                continue

            plot_curves.plot_double_lift_curve(
                pred1,
                pred2,
                data['w_act'].values,
                weight_vals,
                n_bins=n_bins,
                title=f"Double Lift Chart on {data_name}",
                label1=label1,
                label2=label2,
                pred1_weighted=False,
                pred2_weighted=False,
                actual_weighted=True,
                ax=ax,
                show=False,
                style=style,
            )

        plt.subplots_adjust(bottom=0.25, top=0.95, right=0.8, wspace=0.3)
        save_path = self.output_manager.plot_path(
            f'02_{self.model_nme}_dlift_{name1}_vs_{name2}.png')
        if finalize_figure:
            finalize_figure(fig, save_path=save_path, show=True, style=style)
        else:
            plt.savefig(save_path, dpi=300)
            plt.show()
            plt.close(fig)

    # Conversion lift curve plot.
    def plot_conversion_lift(self, model_pred_col: str, n_bins: int = 20):
        if not self.binary_resp_nme:
            print("Error: `binary_resp_nme` not provided at BayesOptModel init; cannot plot conversion lift.")
            return

        if plot_curves is None:
            fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
            datasets = {
                'Train Data': self.train_data,
                'Test Data': self.test_data
            }

            for ax, (data_name, data) in zip(axes, datasets.items()):
                if model_pred_col not in data.columns:
                    print(f"Warning: missing prediction column '{model_pred_col}' in {data_name}. Skip plot.")
                    continue

                # Sort by model prediction and compute bins.
                plot_data = data.sort_values(by=model_pred_col).copy()
                plot_data['cum_weight'] = plot_data[self.weight_nme].cumsum()
                total_weight = plot_data[self.weight_nme].sum()

                if total_weight > EPS:
                    plot_data['bin'] = pd.cut(
                        plot_data['cum_weight'],
                        bins=n_bins,
                        labels=False,
                        right=False
                    )
                else:
                    plot_data['bin'] = 0

                # Aggregate by bins.
                lift_agg = plot_data.groupby('bin').agg(
                    total_weight=(self.weight_nme, 'sum'),
                    actual_conversions=(self.binary_resp_nme, 'sum'),
                    weighted_conversions=('w_binary_act', 'sum'),
                    avg_pred=(model_pred_col, 'mean')
                ).reset_index()

                # Compute conversion rate.
                lift_agg['conversion_rate'] = lift_agg['weighted_conversions'] / \
                    lift_agg['total_weight']

                # Compute overall average conversion rate.
                overall_conversion_rate = data['w_binary_act'].sum(
                ) / data[self.weight_nme].sum()
                ax.axhline(y=overall_conversion_rate, color='gray', linestyle='--',
                           label=f'Overall Avg Rate ({overall_conversion_rate:.2%})')

                ax.plot(lift_agg['bin'], lift_agg['conversion_rate'],
                        marker='o', linestyle='-', label='Actual Conversion Rate')
                ax.set_title(f'Conversion Rate Lift Chart on {data_name}')
                ax.set_xlabel(f'Model Score Decile (based on {model_pred_col})')
                ax.set_ylabel('Conversion Rate')
                ax.grid(True, linestyle='--', alpha=0.6)
                ax.legend()

            plt.tight_layout()
            plt.show()
            return

        fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
        datasets = {
            'Train Data': self.train_data,
            'Test Data': self.test_data
        }

        for ax, (data_name, data) in zip(axes, datasets.items()):
            if model_pred_col not in data.columns:
                print(f"Warning: missing prediction column '{model_pred_col}' in {data_name}. Skip plot.")
                continue

            plot_curves.plot_conversion_lift(
                data[model_pred_col].values,
                data[self.binary_resp_nme].values,
                data[self.weight_nme].values,
                n_bins=n_bins,
                title=f'Conversion Rate Lift Chart on {data_name}',
                ax=ax,
                show=False,
            )

        plt.tight_layout()
        plt.show()

    # ========= Lightweight explainability: Permutation Importance =========
    def compute_permutation_importance(self,
                                       model_key: str,
                                       on_train: bool = True,
                                       metric: Any = "auto",
                                       n_repeats: int = 5,
                                       max_rows: int = 5000,
                                       random_state: Optional[int] = None):
        if explain_permutation is None:
            raise RuntimeError("explain.permutation is not available.")

        model_key = str(model_key)
        data = self.train_data if on_train else self.test_data
        if self.resp_nme not in data.columns:
            raise RuntimeError("Missing response column for permutation importance.")
        y = data[self.resp_nme]
        w = data[self.weight_nme] if self.weight_nme in data.columns else None

        if model_key == "resn":
            if self.resn_best is None:
                raise RuntimeError("ResNet model not trained.")
            X = self.train_oht_scl_data if on_train else self.test_oht_scl_data
            if X is None:
                raise RuntimeError("Missing standardized features for ResNet.")
            X = X[self.var_nmes]
            predict_fn = lambda df: self.resn_best.predict(df)
        elif model_key == "ft":
            if self.ft_best is None:
                raise RuntimeError("FT model not trained.")
            if str(self.config.ft_role) != "model":
                raise RuntimeError("FT role is not 'model'; FT predictions unavailable.")
            X = data[self.factor_nmes]
            geo_tokens = self.train_geo_tokens if on_train else self.test_geo_tokens
            geo_np = None
            if geo_tokens is not None:
                geo_np = geo_tokens.to_numpy(dtype=np.float32, copy=False)
            predict_fn = lambda df, geo=geo_np: self.ft_best.predict(df, geo_tokens=geo)
        elif model_key == "xgb":
            if self.xgb_best is None:
                raise RuntimeError("XGB model not trained.")
            X = data[self.factor_nmes]
            predict_fn = lambda df: self.xgb_best.predict(df)
        else:
            raise ValueError("Unsupported model_key for permutation importance.")

        return explain_permutation.permutation_importance(
            predict_fn,
            X,
            y,
            sample_weight=w,
            metric=metric,
            task_type=self.task_type,
            n_repeats=n_repeats,
            random_state=random_state,
            max_rows=max_rows,
        )

    # ========= Deep explainability: Integrated Gradients =========
    def compute_integrated_gradients_resn(self,
                                          on_train: bool = True,
                                          baseline: Any = None,
                                          steps: int = 50,
                                          batch_size: int = 256,
                                          target: Optional[int] = None):
        if explain_gradients is None:
            raise RuntimeError("explain.gradients is not available.")
        if self.resn_best is None:
            raise RuntimeError("ResNet model not trained.")
        X = self.train_oht_scl_data if on_train else self.test_oht_scl_data
        if X is None:
            raise RuntimeError("Missing standardized features for ResNet.")
        X = X[self.var_nmes]
        return explain_gradients.resnet_integrated_gradients(
            self.resn_best,
            X,
            baseline=baseline,
            steps=steps,
            batch_size=batch_size,
            target=target,
        )

    def compute_integrated_gradients_ft(self,
                                        on_train: bool = True,
                                        geo_tokens: Optional[np.ndarray] = None,
                                        baseline_num: Any = None,
                                        baseline_geo: Any = None,
                                        steps: int = 50,
                                        batch_size: int = 256,
                                        target: Optional[int] = None):
        if explain_gradients is None:
            raise RuntimeError("explain.gradients is not available.")
        if self.ft_best is None:
            raise RuntimeError("FT model not trained.")
        if str(self.config.ft_role) != "model":
            raise RuntimeError("FT role is not 'model'; FT explanations unavailable.")

        data = self.train_data if on_train else self.test_data
        X = data[self.factor_nmes]

        if geo_tokens is None and getattr(self.ft_best, "num_geo", 0) > 0:
            tokens_df = self.train_geo_tokens if on_train else self.test_geo_tokens
            if tokens_df is not None:
                geo_tokens = tokens_df.to_numpy(dtype=np.float32, copy=False)

        return explain_gradients.ft_integrated_gradients(
            self.ft_best,
            X,
            geo_tokens=geo_tokens,
            baseline_num=baseline_num,
            baseline_geo=baseline_geo,
            steps=steps,
            batch_size=batch_size,
            target=target,
        )

    # Save model
    def save_model(self, model_name=None):
        keys = [model_name] if model_name else self.trainers.keys()
        for key in keys:
            if key in self.trainers:
                self.trainers[key].save()
            else:
                if model_name:  # Only warn when the user specifies a model name.
                    print(f"[save_model] Warning: Unknown model key {key}")

    def load_model(self, model_name=None):
        keys = [model_name] if model_name else self.trainers.keys()
        for key in keys:
            if key in self.trainers:
                self.trainers[key].load()
                # Sync context fields.
                trainer = self.trainers[key]
                if trainer.model is not None:
                    setattr(self, f"{key}_best", trainer.model)
                    # For legacy compatibility, also update xxx_load.
                    # Old versions only tracked xgb_load/resn_load/ft_load (not glm_load/gnn_load).
                    if key in ['xgb', 'resn', 'ft', 'gnn']:
                        setattr(self, f"{key}_load", trainer.model)
            else:
                if model_name:
                    print(f"[load_model] Warning: Unknown model key {key}")

    def _sample_rows(self, data: pd.DataFrame, n: int) -> pd.DataFrame:
        if len(data) == 0:
            return data
        return data.sample(min(len(data), n), random_state=self.rand_seed)

    @staticmethod
    def _shap_nsamples(arr: np.ndarray, max_nsamples: int = 300) -> int:
        min_needed = arr.shape[1] + 2
        return max(min_needed, min(max_nsamples, arr.shape[0] * arr.shape[1]))

    def _build_ft_shap_matrix(self, data: pd.DataFrame) -> np.ndarray:
        matrices = []
        for col in self.factor_nmes:
            s = data[col]
            if col in self.cate_list:
                cats = pd.Categorical(
                    s,
                    categories=self.cat_categories_for_shap[col]
                )
                codes = np.asarray(cats.codes, dtype=np.float64).reshape(-1, 1)
                matrices.append(codes)
            else:
                vals = pd.to_numeric(s, errors="coerce")
                arr = vals.to_numpy(dtype=np.float64, copy=True).reshape(-1, 1)
                matrices.append(arr)
        X_mat = np.concatenate(matrices, axis=1)  # Result shape (N, F)
        return X_mat

    def _decode_ft_shap_matrix_to_df(self, X_mat: np.ndarray) -> pd.DataFrame:
        data_dict = {}
        for j, col in enumerate(self.factor_nmes):
            col_vals = X_mat[:, j]
            if col in self.cate_list:
                cats = self.cat_categories_for_shap[col]
                codes = np.round(col_vals).astype(int)
                codes = np.clip(codes, -1, len(cats) - 1)
                cat_series = pd.Categorical.from_codes(
                    codes,
                    categories=cats
                )
                data_dict[col] = cat_series
            else:
                data_dict[col] = col_vals.astype(float)

        df = pd.DataFrame(data_dict, columns=self.factor_nmes)
        for col in self.cate_list:
            if col in df.columns:
                df[col] = df[col].astype("category")
        return df

    def _build_glm_design(self, data: pd.DataFrame) -> pd.DataFrame:
        X = data[self.var_nmes]
        return sm.add_constant(X, has_constant='add')

    def _compute_shap_core(self,
                           model_key: str,
                           n_background: int,
                           n_samples: int,
                           on_train: bool,
                           X_df: pd.DataFrame,
                           prep_fn,
                           predict_fn,
                           cleanup_fn=None):
        if explain_shap is None:
            raise RuntimeError("explain.shap_utils is not available.")
        return explain_shap.compute_shap_core(
            self,
            model_key,
            n_background,
            n_samples,
            on_train,
            X_df=X_df,
            prep_fn=prep_fn,
            predict_fn=predict_fn,
            cleanup_fn=cleanup_fn,
        )

    # ========= GLM SHAP explainability =========
    def compute_shap_glm(self, n_background: int = 500,
                         n_samples: int = 200,
                         on_train: bool = True):
        if explain_shap is None:
            raise RuntimeError("explain.shap_utils is not available.")
        self.shap_glm = explain_shap.compute_shap_glm(
            self,
            n_background=n_background,
            n_samples=n_samples,
            on_train=on_train,
        )
        return self.shap_glm

    # ========= XGBoost SHAP explainability =========
    def compute_shap_xgb(self, n_background: int = 500,
                         n_samples: int = 200,
                         on_train: bool = True):
        if explain_shap is None:
            raise RuntimeError("explain.shap_utils is not available.")
        self.shap_xgb = explain_shap.compute_shap_xgb(
            self,
            n_background=n_background,
            n_samples=n_samples,
            on_train=on_train,
        )
        return self.shap_xgb

    # ========= ResNet SHAP explainability =========
    def _resn_predict_wrapper(self, X_np):
        model = self.resn_best.resnet.to("cpu")
        with torch.no_grad():
            X_tensor = torch.tensor(X_np, dtype=torch.float32)
            y_pred = model(X_tensor).cpu().numpy()
        y_pred = np.clip(y_pred, 1e-6, None)
        return y_pred.reshape(-1)

    def compute_shap_resn(self, n_background: int = 500,
                          n_samples: int = 200,
                          on_train: bool = True):
        if explain_shap is None:
            raise RuntimeError("explain.shap_utils is not available.")
        self.shap_resn = explain_shap.compute_shap_resn(
            self,
            n_background=n_background,
            n_samples=n_samples,
            on_train=on_train,
        )
        return self.shap_resn

    # ========= FT-Transformer SHAP explainability =========
    def _ft_shap_predict_wrapper(self, X_mat: np.ndarray) -> np.ndarray:
        df_input = self._decode_ft_shap_matrix_to_df(X_mat)
        y_pred = self.ft_best.predict(df_input)
        return np.asarray(y_pred, dtype=np.float64).reshape(-1)

    def compute_shap_ft(self, n_background: int = 500,
                        n_samples: int = 200,
                        on_train: bool = True):
        if explain_shap is None:
            raise RuntimeError("explain.shap_utils is not available.")
        self.shap_ft = explain_shap.compute_shap_ft(
            self,
            n_background=n_background,
            n_samples=n_samples,
            on_train=on_train,
        )
        return self.shap_ft
