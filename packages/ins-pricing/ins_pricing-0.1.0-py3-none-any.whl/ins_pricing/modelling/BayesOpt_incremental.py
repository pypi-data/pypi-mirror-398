"""Incremental training harness built on top of ``ins_pricing.bayesopt``
(compat via ``BayesOpt.py``).

This utility lets you append new observations to an existing dataset,
reuse previously tuned hyperparameters and retrain a subset of models
without re-running the full Optuna search. It can operate on a directory
of per-model incremental CSVs or a single incremental file when updating
one dataset.

Example:
    python ins_pricing/modelling/BayesOpt_incremental.py \
        --config-json ins_pricing/modelling/demo/config_incremental_template.json \
        --incremental-dir ./incremental_batches \
        --merge-keys policy_id vehicle_id \
        --model-keys glm xgb resn --plot-curves
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

try:
    from . import bayesopt as ropt  # type: ignore
    from .cli_common import (  # type: ignore
        PLOT_MODEL_LABELS,
        PYTORCH_TRAINERS,
        build_model_names,
        dedupe_preserve_order,
        load_config_json,
        normalize_config_paths,
        parse_model_pairs,
        resolve_config_path,
        resolve_path,
        set_env,
    )
except Exception:  # pragma: no cover
    try:
        import bayesopt as ropt  # type: ignore
        from cli_common import (  # type: ignore
            PLOT_MODEL_LABELS,
            PYTORCH_TRAINERS,
            build_model_names,
            dedupe_preserve_order,
            load_config_json,
            normalize_config_paths,
            parse_model_pairs,
            resolve_config_path,
            resolve_path,
            set_env,
        )
    except Exception:
        try:
            import ins_pricing.bayesopt as ropt  # type: ignore
            from ins_pricing.cli_common import (  # type: ignore
                PLOT_MODEL_LABELS,
                PYTORCH_TRAINERS,
                build_model_names,
                dedupe_preserve_order,
                load_config_json,
                normalize_config_paths,
                parse_model_pairs,
                resolve_config_path,
                resolve_path,
                set_env,
            )
        except Exception:
            import BayesOpt as ropt  # type: ignore
            from cli_common import (  # type: ignore
                PLOT_MODEL_LABELS,
                PYTORCH_TRAINERS,
                build_model_names,
                dedupe_preserve_order,
                load_config_json,
                normalize_config_paths,
                parse_model_pairs,
                resolve_config_path,
                resolve_path,
                set_env,
            )


def _log(message: str) -> None:
    print(f"[Incremental] {message}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Incrementally retrain BayesOpt models using new batches of data."
    )
    parser.add_argument(
        "--config-json",
        required=True,
        help="Path to the JSON config that BayesOpt_entry.py uses."
    )
    parser.add_argument(
        "--model-names",
        nargs="+",
        default=None,
        help="Optional subset of dataset names to update (defaults to model_list/model_categories Cartesian product)."
    )
    parser.add_argument(
        "--model-keys",
        nargs="+",
        default=["glm", "xgb", "resn", "ft"],
        choices=["glm", "xgb", "resn", "ft", "gnn", "all"],
        help="Which trainers to run for each dataset."
    )
    parser.add_argument(
        "--incremental-dir",
        type=Path,
        default=None,
        help="Directory containing <model_name> incremental CSVs."
    )
    parser.add_argument(
        "--incremental-file",
        type=Path,
        default=None,
        help="Single incremental CSV (requires --model-names with exactly one entry)."
    )
    parser.add_argument(
        "--incremental-template",
        default="{model_name}_incremental.csv",
        help="Filename template when --incremental-dir is provided."
    )
    parser.add_argument(
        "--merge-keys",
        nargs="+",
        default=None,
        help="Column(s) used to drop duplicate rows after merging base and incremental data."
    )
    parser.add_argument(
        "--dedupe-keep",
        choices=["first", "last"],
        default="last",
        help="How pandas.drop_duplicates resolves conflicts on merge keys."
    )
    parser.add_argument(
        "--timestamp-col",
        default=None,
        help="Optional column used to sort rows before deduplication."
    )
    parser.add_argument(
        "--timestamp-descending",
        action="store_true",
        help="Sort timestamp column in descending order before deduplication."
    )
    parser.add_argument(
        "--min-new-rows",
        type=int,
        default=1,
        help="Skip training if fewer new rows than this arrive (unless --train-without-incremental)."
    )
    parser.add_argument(
        "--train-without-incremental",
        action="store_true",
        help="Always retrain even when no incremental file is present."
    )
    parser.add_argument(
        "--strict-incremental",
        action="store_true",
        help="Raise an error when a dataset is missing its incremental CSV instead of skipping it."
    )
    parser.add_argument(
        "--tag-new-column",
        default=None,
        help="If set, store 1 for incremental rows and 0 for historical rows in this column."
    )
    parser.add_argument(
        "--max-evals",
        type=int,
        default=25,
        help="Optuna trial count when retuning is required."
    )
    parser.add_argument(
        "--retune-missing",
        dest="retune_missing",
        action="store_true",
        default=True,
        help="Retune models whose best-params CSV is unavailable (default)."
    )
    parser.add_argument(
        "--skip-retune-missing",
        dest="retune_missing",
        action="store_false",
        help="Do not retune when best params are missing; such models are skipped."
    )
    parser.add_argument(
        "--force-retune",
        action="store_true",
        help="Run Optuna tuning even if historical best params exist."
    )
    parser.add_argument(
        "--prop-test",
        type=float,
        default=None,
        help="Override the test split proportion defined in the config file."
    )
    parser.add_argument(
        "--rand-seed",
        type=int,
        default=None,
        help="Override the random seed defined in the config."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Override the epoch count from the config."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override the BayesOpt output root (models/results/plots)."
    )
    parser.add_argument(
        "--update-base-data",
        action="store_true",
        help="Overwrite the base CSVs with the merged dataset after a successful update."
    )
    parser.add_argument(
        "--persist-merged-dir",
        type=Path,
        default=None,
        help="Optional directory to store the merged dataset snapshots."
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=None,
        help="Write a JSON summary of processed datasets to this path."
    )
    parser.add_argument(
        "--plot-curves",
        action="store_true",
        help="Run one-way/lift plots after training (config plot settings also apply)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Merge and report counts but skip training, saving and plotting."
    )
    args = parser.parse_args()

    if args.incremental_file and args.incremental_dir:
        parser.error("Use either --incremental-dir or --incremental-file, not both.")
    if args.incremental_file and args.model_names and len(args.model_names) != 1:
        parser.error("--incremental-file can only be used when updating exactly one model.")
    if (not args.incremental_dir and not args.incremental_file) and not args.train_without_incremental:
        parser.error(
            "Provide --incremental-dir/--incremental-file or enable --train-without-incremental."
        )
    return args


def _plot_curves_for_model(model: ropt.BayesOptModel, trained: List[str], cfg: Dict[str, Any]) -> None:
    plot_cfg = cfg.get("plot", {})
    legacy_flags = {
        "glm": cfg.get("plot_lift_glm", False),
        "xgb": cfg.get("plot_lift_xgb", False),
        "resn": cfg.get("plot_lift_resn", False),
        "ft": cfg.get("plot_lift_ft", False),
    }
    plot_enabled = plot_cfg.get("enable", any(legacy_flags.values()))
    if not plot_enabled:
        return

    n_bins = int(plot_cfg.get("n_bins", 10))
    oneway_enabled = plot_cfg.get("oneway", True)
    available = dedupe_preserve_order([k for k in trained if k in PLOT_MODEL_LABELS])

    if oneway_enabled:
        model.plot_oneway(n_bins=n_bins)
    if not available:
        return

    lift_models = plot_cfg.get("lift_models")
    if lift_models is None:
        lift_models = [m for m, flag in legacy_flags.items() if flag] or available
    lift_models = dedupe_preserve_order([m for m in lift_models if m in available])

    for key in lift_models:
        label, pred_nme = PLOT_MODEL_LABELS[key]
        model.plot_lift(model_label=label, pred_nme=pred_nme, n_bins=n_bins)

    if not plot_cfg.get("double_lift", True) or len(available) < 2:
        return

    raw_pairs = plot_cfg.get("double_lift_pairs")
    if raw_pairs:
        pairs = [
            (a, b)
            for a, b in parse_model_pairs(raw_pairs)
            if a in available and b in available and a != b
        ]
    else:
        pairs = [(a, b) for i, a in enumerate(available) for b in available[i + 1 :]]
    for first, second in pairs:
        model.plot_dlift([first, second], n_bins=n_bins)


def _coerce_scalar(value: Any) -> Any:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"", "none", "nan"}:
            return None
        if lowered in {"true", "false"}:
            return lowered == "true"
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def _load_best_params(model: ropt.BayesOptModel, trainer, silent: bool = False) -> Optional[Dict[str, Any]]:
    label = trainer.label.lower()
    result_dir = Path(model.output_manager.result_dir)
    path = result_dir / f"{model.model_nme}_bestparams_{label}.csv"
    if not path.exists():
        if not silent:
            _log(f"No historical params found for {model.model_nme}/{label} at {path}.")
        return None
    try:
        params_raw = ropt.IOUtils.load_params_file(str(path))
    except Exception:
        return None
    return {
        key: _coerce_scalar(val)
        for key, val in (params_raw or {}).items()
        if not pd.isna(val)
    }


def _to_serializable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_serializable(v) for v in obj]
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            return str(obj)
    return obj


class IncrementalUpdateRunner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        script_dir = Path(__file__).resolve().parent
        self.config_path = resolve_config_path(args.config_json, script_dir)
        cfg = load_config_json(
            self.config_path,
            required_keys=[
                "data_dir",
                "model_list",
                "model_categories",
                "target",
                "weight",
                "feature_list",
                "categorical_features",
            ],
        )
        self.cfg = normalize_config_paths(cfg, self.config_path)
        set_env(self.cfg.get("env", {}))
        self.data_dir = Path(self.cfg["data_dir"])
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.prop_test = args.prop_test if args.prop_test is not None else self.cfg.get("prop_test", 0.25)
        self.rand_seed = args.rand_seed if args.rand_seed is not None else self.cfg.get("rand_seed", 13)
        self.epochs = args.epochs if args.epochs is not None else self.cfg.get("epochs", 50)
        self.plot_requested = bool(args.plot_curves or self.cfg.get("plot_curves", False))
        self.model_names = self._resolve_model_names(args.model_names)
        self.merge_keys = list(args.merge_keys or [])
        self.timestamp_col = args.timestamp_col
        self.timestamp_ascending = not args.timestamp_descending
        output_root = args.output_dir or self.cfg.get("output_dir")
        if isinstance(output_root, Path) and not output_root.is_absolute():
            output_root = (self.config_path.parent / output_root).resolve()
        if isinstance(output_root, str) and output_root.strip():
            resolved = resolve_path(output_root, self.config_path.parent)
            if resolved is not None:
                output_root = str(resolved)
        self.output_root = output_root

        self.incremental_dir = None
        if args.incremental_dir is not None:
            self.incremental_dir = args.incremental_dir
            if not self.incremental_dir.is_absolute():
                self.incremental_dir = (self.config_path.parent / self.incremental_dir).resolve()
            else:
                self.incremental_dir = self.incremental_dir.resolve()
        self.incremental_file = None
        if args.incremental_file is not None:
            self.incremental_file = args.incremental_file
            if not self.incremental_file.is_absolute():
                self.incremental_file = (self.config_path.parent / self.incremental_file).resolve()
            else:
                self.incremental_file = self.incremental_file.resolve()
        self.summary_records: List[Dict[str, Any]] = []
        self.binary_resp = self.cfg.get("binary_resp_nme") or self.cfg.get("binary_target")

        if self.incremental_file and len(self.model_names) != 1:
            raise ValueError("--incremental-file can only be used when exactly one model name is targeted.")

    def _resolve_model_names(self, override: Optional[Sequence[str]]) -> List[str]:
        if override:
            return dedupe_preserve_order([str(item) for item in override])
        prefixes = self.cfg["model_list"]
        suffixes = self.cfg["model_categories"]
        return build_model_names(prefixes, suffixes)

    def _load_incremental_df(self, model_name: str) -> Tuple[Optional[pd.DataFrame], Optional[Path]]:
        path: Optional[Path] = None
        if self.incremental_file:
            path = self.incremental_file
        elif self.incremental_dir:
            rel = self.args.incremental_template.format(model_name=model_name)
            path = (self.incremental_dir / rel).resolve()
        if not path or not path.exists():
            return None, None
        try:
            df = pd.read_csv(path, low_memory=False)
        except pd.errors.EmptyDataError:
            _log(f"Incremental file {path} is empty; treating as no-op.")
            return None, path
        return df, path

    def _merge_frames(self, base_df: pd.DataFrame, inc_df: Optional[pd.DataFrame]) -> pd.DataFrame:
        if inc_df is None or inc_df.empty:
            merged = base_df.copy(deep=True)
            return merged.reset_index(drop=True)
        frames = []
        tag = self.args.tag_new_column
        if tag:
            base_part = base_df.copy(deep=True)
            base_part[tag] = 0
            inc_part = inc_df.copy(deep=True)
            inc_part[tag] = 1
            frames = [base_part, inc_part]
        else:
            frames = [base_df, inc_df]
        merged = pd.concat(frames, ignore_index=True, sort=False)
        if self.timestamp_col and self.timestamp_col in merged.columns:
            merged = merged.sort_values(
                self.timestamp_col,
                ascending=self.timestamp_ascending,
                kind="mergesort",
            )
        if self.merge_keys:
            missing = [col for col in self.merge_keys if col not in merged.columns]
            if missing:
                raise KeyError(f"Merge keys {missing} not found in merged frame for {self.merge_keys}.")
            merged = merged.drop_duplicates(subset=self.merge_keys, keep=self.args.dedupe_keep)
        return merged.reset_index(drop=True)

    def _should_train(self, new_rows: int) -> bool:
        if self.args.train_without_incremental:
            return True
        min_needed = max(0, self.args.min_new_rows)
        return new_rows >= min_needed

    def _write_dataset(self, df: pd.DataFrame, dest: Path, reason: str) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(dest, index=False)
        _log(f"Wrote {len(df)} rows to {dest} ({reason}).")

    def _prepare_splits(self, merged: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        if not 0 < self.prop_test < 1:
            raise ValueError(f"prop_test must fall in (0, 1); got {self.prop_test}.")
        if len(merged) < 2:
            raise ValueError("Need at least two rows to form a train/test split.")
        train_df, test_df = train_test_split(
            merged,
            test_size=self.prop_test,
            random_state=self.rand_seed,
        )
        return train_df.reset_index(drop=True), test_df.reset_index(drop=True)

    def _requested_model_keys(self, trainer_map: Dict[str, Any]) -> List[str]:
        requested = self.args.model_keys
        if "all" in requested:
            requested = ["glm", "xgb", "resn", "ft", "gnn"]
        requested = dedupe_preserve_order(requested)
        missing = [key for key in requested if key not in trainer_map]
        for key in missing:
            _log(f"Trainer '{key}' is not available for this context and will be skipped.")
        return [key for key in requested if key in trainer_map]

    def _train_single_model(
        self,
        model_name: str,
        merged: pd.DataFrame,
        new_rows: int,
        incremental_path: Optional[Path],
    ) -> Dict[str, Any]:
        merged = merged.copy(deep=True)
        merged.fillna(0, inplace=True)
        train_df, test_df = self._prepare_splits(merged)
        model = ropt.BayesOptModel(
            train_df,
            test_df,
            model_name,
            self.cfg["target"],
            self.cfg["weight"],
            self.cfg["feature_list"],
            task_type=self.cfg.get("task_type", "regression"),
            binary_resp_nme=self.binary_resp,
            cate_list=self.cfg.get("categorical_features"),
            prop_test=self.prop_test,
            rand_seed=self.rand_seed,
            epochs=self.epochs,
            use_resn_data_parallel=self.cfg.get("use_resn_data_parallel", False),
            use_ft_data_parallel=self.cfg.get("use_ft_data_parallel", True),
            use_gnn_data_parallel=self.cfg.get("use_gnn_data_parallel", False),
            use_resn_ddp=self.cfg.get("use_resn_ddp", False),
            use_ft_ddp=self.cfg.get("use_ft_ddp", False),
            use_gnn_ddp=self.cfg.get("use_gnn_ddp", False),
            output_dir=str(self.output_root) if self.output_root else None,
            xgb_max_depth_max=int(self.cfg.get("xgb_max_depth_max", 25)),
            xgb_n_estimators_max=int(self.cfg.get("xgb_n_estimators_max", 500)),
            resn_weight_decay=self.cfg.get("resn_weight_decay"),
            final_ensemble=bool(self.cfg.get("final_ensemble", False)),
            final_ensemble_k=int(self.cfg.get("final_ensemble_k", 3)),
            final_refit=bool(self.cfg.get("final_refit", True)),
            optuna_storage=self.cfg.get("optuna_storage"),
            optuna_study_prefix=self.cfg.get("optuna_study_prefix"),
            best_params_files=self.cfg.get("best_params_files"),
            reuse_best_params=bool(self.cfg.get("reuse_best_params", False)),
            gnn_use_approx_knn=self.cfg.get("gnn_use_approx_knn", True),
            gnn_approx_knn_threshold=self.cfg.get("gnn_approx_knn_threshold", 50000),
            gnn_graph_cache=self.cfg.get("gnn_graph_cache"),
            gnn_max_gpu_knn_nodes=self.cfg.get("gnn_max_gpu_knn_nodes", 200000),
            gnn_knn_gpu_mem_ratio=self.cfg.get("gnn_knn_gpu_mem_ratio", 0.9),
            gnn_knn_gpu_mem_overhead=self.cfg.get("gnn_knn_gpu_mem_overhead", 2.0),
            ft_role=str(self.cfg.get("ft_role", "model")),
            ft_feature_prefix=str(self.cfg.get("ft_feature_prefix", "ft_emb")),
            ft_num_numeric_tokens=self.cfg.get("ft_num_numeric_tokens"),
            infer_categorical_max_unique=int(self.cfg.get("infer_categorical_max_unique", 50)),
            infer_categorical_max_ratio=float(self.cfg.get("infer_categorical_max_ratio", 0.05)),
        )

        requested_keys = self._requested_model_keys(model.trainers)
        executed_keys: List[str] = []
        param_sources: Dict[str, str] = {}

        if self.args.dry_run:
            _log(f"Dry run: would train {requested_keys} for {model_name}.")
            return {
                "executed_keys": executed_keys,
                "param_sources": param_sources,
                "model": model,
            }

        if self.args.force_retune and self.args.max_evals <= 0:
            raise ValueError("force_retune requires --max-evals > 0.")

        force_retune = bool(self.args.force_retune)
        if force_retune:
            model.config.reuse_best_params = False
            model.config.best_params_files = {}

        ft_role = str(getattr(model.config, "ft_role", "model"))
        if ft_role != "model" and "ft" in requested_keys:
            requested_keys = ["ft"] + [k for k in requested_keys if k != "ft"]

        for key in requested_keys:
            trainer = model.trainers[key]

            if force_retune:
                trainer.best_params = None
                trainer.best_trial = None
                param_sources[key] = "retune"
            else:
                best_params = _load_best_params(model, trainer, silent=True)
                if best_params:
                    trainer.best_params = best_params
                    trainer.best_trial = None
                    param_sources[key] = "loaded"
                else:
                    if not self.args.retune_missing:
                        _log(
                            f"Skipping {model_name}/{key}: no best params and retuning disabled."
                        )
                        continue
                    param_sources[key] = "retune"

            if (trainer.best_params is None) and self.args.max_evals <= 0:
                raise ValueError("--max-evals must be positive when retuning is requested.")

            model.optimize_model(key, max_evals=self.args.max_evals)
            trainer.save()
            executed_keys.append(key)
            if key in PYTORCH_TRAINERS:
                ropt.free_cuda()

            snapshot = {
                "mode": "incremental_train",
                "model_name": model_name,
                "model_key": key,
                "timestamp": datetime.now().isoformat(),
                "param_source": param_sources[key],
                "best_params": _to_serializable(trainer.best_params or {}),
                "incremental_rows": new_rows,
                "train_rows": len(model.train_data),
                "test_rows": len(model.test_data),
                "incremental_path": str(incremental_path) if incremental_path else None,
                "config": asdict(model.config),
            }
            model.version_manager.save(f"{model_name}_{key}_incremental", snapshot)

        if not executed_keys:
            _log(f"No trainers executed for {model_name}.")

        return {
            "executed_keys": executed_keys,
            "param_sources": param_sources,
            "model": model,
        }

    def process(self) -> None:
        total_trained = 0
        for model_name in self.model_names:
            total_trained += self._process_single_model(model_name)
        if self.args.summary_json and self.summary_records:
            summary_path = self.args.summary_json.resolve()
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_payload = _to_serializable(self.summary_records)
            summary_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")
            _log(f"Summary written to {summary_path}.")
        _log(f"Finished incremental update for {total_trained} dataset(s).")

    def _process_single_model(self, model_name: str) -> int:
        base_path = self.data_dir / f"{model_name}.csv"
        if not base_path.exists():
            _log(f"Base dataset {base_path} not found; skipping {model_name}.")
            self.summary_records.append({
                "model_name": model_name,
                "status": "missing_base",
            })
            return 0

        base_df = pd.read_csv(base_path, low_memory=False)
        inc_df, inc_path = self._load_incremental_df(model_name)
        if inc_df is None and self.incremental_dir and self.args.strict_incremental and not self.args.train_without_incremental:
            raise FileNotFoundError(f"Missing incremental file for {model_name} under {self.incremental_dir}.")

        new_rows = 0 if inc_df is None else len(inc_df)
        _log(f"{model_name}: {len(base_df)} base rows, {new_rows} incremental rows.")
        merged_df = self._merge_frames(base_df, inc_df)
        merged_df.fillna(0, inplace=True)

        if self.args.update_base_data and not self.args.dry_run:
            self._write_dataset(merged_df, base_path, "update_base_data")
        if self.args.persist_merged_dir and not self.args.dry_run:
            dest = Path(self.args.persist_merged_dir).resolve() / f"{model_name}.csv"
            self._write_dataset(merged_df, dest, "persist_merged_dir")

        if not self._should_train(new_rows):
            _log(f"{model_name}: below min_new_rows ({self.args.min_new_rows}); skipping retrain.")
            self.summary_records.append({
                "model_name": model_name,
                "status": "skipped_no_incremental",
                "new_rows": new_rows,
                "total_rows": len(merged_df),
            })
            return 0

        try:
            train_result = self._train_single_model(model_name, merged_df, new_rows, inc_path)
        except Exception as exc:
            _log(f"Training failed for {model_name}: {exc}")
            self.summary_records.append({
                "model_name": model_name,
                "status": "failed",
                "error": str(exc),
                "new_rows": new_rows,
                "total_rows": len(merged_df),
            })
            return 0

        executed = train_result["executed_keys"]
        param_sources = train_result["param_sources"]
        model = train_result["model"]
        status = "dry_run" if self.args.dry_run else "trained"

        summary = {
            "model_name": model_name,
            "status": status,
            "trained_models": executed,
            "param_sources": param_sources,
            "new_rows": new_rows,
            "total_rows": len(merged_df),
            "incremental_path": str(inc_path) if inc_path else None,
        }
        self.summary_records.append(summary)

        if not self.args.dry_run and self.plot_requested and executed:
            _plot_curves_for_model(model, executed, self.cfg)

        return 1 if executed else 0


def main() -> None:
    args = _parse_args()
    runner = IncrementalUpdateRunner(args)
    runner.process()


if __name__ == "__main__":
    main()
