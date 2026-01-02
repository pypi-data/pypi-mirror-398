"""Config-driven explain runner for trained BayesOpt models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

try:
    from . import bayesopt as ropt  # type: ignore
    from .cli_common import (  # type: ignore
        build_model_names,
        dedupe_preserve_order,
        load_config_json,
        normalize_config_paths,
        resolve_config_path,
        resolve_path,
        set_env,
    )
except Exception:  # pragma: no cover
    try:
        import bayesopt as ropt  # type: ignore
        from cli_common import (  # type: ignore
            build_model_names,
            dedupe_preserve_order,
            load_config_json,
            normalize_config_paths,
            resolve_config_path,
            resolve_path,
            set_env,
        )
    except Exception:
        import ins_pricing.bayesopt as ropt  # type: ignore
        from ins_pricing.cli_common import (  # type: ignore
            build_model_names,
            dedupe_preserve_order,
            load_config_json,
            normalize_config_paths,
            resolve_config_path,
            resolve_path,
            set_env,
        )


_SUPPORTED_METHODS = {"permutation", "shap", "integrated_gradients"}
_METHOD_ALIASES = {
    "ig": "integrated_gradients",
    "integrated": "integrated_gradients",
    "intgrad": "integrated_gradients",
}


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(value))


def _load_dataset(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, low_memory=False)
    raw = raw.copy()
    for col in raw.columns:
        s = raw[col]
        if pd.api.types.is_numeric_dtype(s):
            raw[col] = pd.to_numeric(s, errors="coerce").fillna(0)
        else:
            raw[col] = s.astype("object").fillna("<NA>")
    return raw


def _resolve_path_value(
    value: Any,
    *,
    model_name: str,
    base_dir: Path,
    data_dir: Optional[Path] = None,
) -> Optional[Path]:
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get(model_name)
    if value is None:
        return None
    path_str = str(value)
    try:
        path_str = path_str.format(model_name=model_name)
    except Exception:
        pass
    if data_dir is not None and not Path(path_str).is_absolute():
        candidate = data_dir / path_str
        if candidate.exists():
            return candidate.resolve()
    resolved = resolve_path(path_str, base_dir)
    if resolved is None:
        return None
    return resolved


def _normalize_methods(raw: Sequence[str]) -> List[str]:
    methods: List[str] = []
    for item in raw:
        key = str(item).strip().lower()
        if not key:
            continue
        key = _METHOD_ALIASES.get(key, key)
        if key not in _SUPPORTED_METHODS:
            raise ValueError(f"Unsupported explain method: {item}")
        methods.append(key)
    return dedupe_preserve_order(methods)


def _save_series(series: pd.Series, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    series.to_frame(name="importance").to_csv(path, index=True)


def _save_df(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _shap_importance(values: Any, feature_names: Sequence[str]) -> pd.Series:
    if isinstance(values, list):
        values = values[0]
    arr = np.asarray(values)
    if arr.ndim == 3:
        arr = arr[0]
    scores = np.mean(np.abs(arr), axis=0)
    return pd.Series(scores, index=list(feature_names)).sort_values(ascending=False)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run explainability (permutation/SHAP/IG) on trained models."
    )
    parser.add_argument(
        "--config-json",
        required=True,
        help="Path to config.json (same schema as training).",
    )
    parser.add_argument(
        "--model-keys",
        nargs="+",
        default=None,
        choices=["glm", "xgb", "resn", "ft", "gnn", "all"],
        help="Model keys to load for explanation (default from config.explain.model_keys).",
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        default=None,
        help="Explain methods: permutation, shap, integrated_gradients (default from config.explain.methods).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Override output root for loading models/results.",
    )
    parser.add_argument(
        "--eval-path",
        default=None,
        help="Override validation CSV path (supports {model_name}).",
    )
    parser.add_argument(
        "--on-train",
        action="store_true",
        help="Explain on train split instead of validation/test.",
    )
    parser.add_argument(
        "--save-dir",
        default=None,
        help="Override output directory for explanation artifacts.",
    )
    return parser.parse_args()


def _explain_for_model(
    model: ropt.BayesOptModel,
    *,
    model_name: str,
    model_keys: List[str],
    methods: List[str],
    on_train: bool,
    save_dir: Path,
    explain_cfg: Dict[str, Any],
) -> None:
    perm_cfg = dict(explain_cfg.get("permutation") or {})
    shap_cfg = dict(explain_cfg.get("shap") or {})
    ig_cfg = dict(explain_cfg.get("integrated_gradients") or {})

    perm_metric = perm_cfg.get("metric", explain_cfg.get("metric", "auto"))
    perm_repeats = int(perm_cfg.get("n_repeats", 5))
    perm_max_rows = perm_cfg.get("max_rows", 5000)
    perm_random_state = perm_cfg.get("random_state", None)

    shap_background = int(shap_cfg.get("n_background", 500))
    shap_samples = int(shap_cfg.get("n_samples", 200))
    shap_save_values = bool(shap_cfg.get("save_values", False))

    ig_steps = int(ig_cfg.get("steps", 50))
    ig_batch_size = int(ig_cfg.get("batch_size", 256))
    ig_target = ig_cfg.get("target", None)
    ig_baseline = ig_cfg.get("baseline", None)
    ig_baseline_num = ig_cfg.get("baseline_num", None)
    ig_baseline_geo = ig_cfg.get("baseline_geo", None)
    ig_save_values = bool(ig_cfg.get("save_values", False))

    for key in model_keys:
        trainer = model.trainers.get(key)
        if trainer is None:
            print(f"[Explain] Skip {model_name}/{key}: trainer not available.")
            continue
        model.load_model(key)
        trained_model = getattr(model, f"{key}_best", None)
        if trained_model is None:
            print(f"[Explain] Skip {model_name}/{key}: model not loaded.")
            continue

        if key == "ft" and str(model.config.ft_role) != "model":
            print(f"[Explain] Skip {model_name}/ft: ft_role != 'model'.")
            continue

        for method in methods:
            if method == "permutation" and key not in {"xgb", "resn", "ft"}:
                print(f"[Explain] Skip permutation for {model_name}/{key}.")
                continue
            if method == "shap" and key not in {"glm", "xgb", "resn", "ft"}:
                print(f"[Explain] Skip shap for {model_name}/{key}.")
                continue
            if method == "integrated_gradients" and key not in {"resn", "ft"}:
                print(f"[Explain] Skip integrated gradients for {model_name}/{key}.")
                continue

            if method == "permutation":
                try:
                    result = model.compute_permutation_importance(
                        key,
                        on_train=on_train,
                        metric=perm_metric,
                        n_repeats=perm_repeats,
                        max_rows=perm_max_rows,
                        random_state=perm_random_state,
                    )
                except Exception as exc:
                    print(f"[Explain] permutation failed for {model_name}/{key}: {exc}")
                    continue
                out_path = save_dir / f"{_safe_name(model_name)}_{key}_permutation.csv"
                _save_df(result, out_path)
                print(f"[Explain] Saved permutation -> {out_path}")

            if method == "shap":
                try:
                    if key == "glm":
                        shap_result = model.compute_shap_glm(
                            n_background=shap_background,
                            n_samples=shap_samples,
                            on_train=on_train,
                        )
                    elif key == "xgb":
                        shap_result = model.compute_shap_xgb(
                            n_background=shap_background,
                            n_samples=shap_samples,
                            on_train=on_train,
                        )
                    elif key == "resn":
                        shap_result = model.compute_shap_resn(
                            n_background=shap_background,
                            n_samples=shap_samples,
                            on_train=on_train,
                        )
                    else:
                        shap_result = model.compute_shap_ft(
                            n_background=shap_background,
                            n_samples=shap_samples,
                            on_train=on_train,
                        )
                except Exception as exc:
                    print(f"[Explain] shap failed for {model_name}/{key}: {exc}")
                    continue

                shap_values = shap_result.get("shap_values")
                X_explain = shap_result.get("X_explain")
                feature_names = (
                    list(X_explain.columns)
                    if isinstance(X_explain, pd.DataFrame)
                    else list(model.factor_nmes)
                )
                importance = _shap_importance(shap_values, feature_names)
                out_path = save_dir / f"{_safe_name(model_name)}_{key}_shap_importance.csv"
                _save_series(importance, out_path)
                print(f"[Explain] Saved SHAP importance -> {out_path}")

                if shap_save_values:
                    values_path = save_dir / f"{_safe_name(model_name)}_{key}_shap_values.npy"
                    np.save(values_path, np.array(shap_values, dtype=object), allow_pickle=True)
                    if isinstance(X_explain, pd.DataFrame):
                        x_path = save_dir / f"{_safe_name(model_name)}_{key}_shap_X.csv"
                        _save_df(X_explain, x_path)
                    meta_path = save_dir / f"{_safe_name(model_name)}_{key}_shap_meta.json"
                    meta = {
                        "base_value": shap_result.get("base_value"),
                        "n_samples": int(len(X_explain)) if X_explain is not None else None,
                    }
                    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

            if method == "integrated_gradients":
                try:
                    if key == "resn":
                        ig_result = model.compute_integrated_gradients_resn(
                            on_train=on_train,
                            baseline=ig_baseline,
                            steps=ig_steps,
                            batch_size=ig_batch_size,
                            target=ig_target,
                        )
                        series = ig_result.get("importance")
                        if isinstance(series, pd.Series):
                            out_path = save_dir / f"{_safe_name(model_name)}_{key}_ig_importance.csv"
                            _save_series(series, out_path)
                            print(f"[Explain] Saved IG importance -> {out_path}")
                        if ig_save_values and "attributions" in ig_result:
                            attr_path = save_dir / f"{_safe_name(model_name)}_{key}_ig_attributions.npy"
                            np.save(attr_path, ig_result.get("attributions"))
                    else:
                        ig_result = model.compute_integrated_gradients_ft(
                            on_train=on_train,
                            baseline_num=ig_baseline_num,
                            baseline_geo=ig_baseline_geo,
                            steps=ig_steps,
                            batch_size=ig_batch_size,
                            target=ig_target,
                        )
                        series_num = ig_result.get("importance_num")
                        series_geo = ig_result.get("importance_geo")
                        if isinstance(series_num, pd.Series):
                            out_path = save_dir / f"{_safe_name(model_name)}_{key}_ig_num_importance.csv"
                            _save_series(series_num, out_path)
                            print(f"[Explain] Saved IG num importance -> {out_path}")
                        if isinstance(series_geo, pd.Series):
                            out_path = save_dir / f"{_safe_name(model_name)}_{key}_ig_geo_importance.csv"
                            _save_series(series_geo, out_path)
                            print(f"[Explain] Saved IG geo importance -> {out_path}")
                        if ig_save_values:
                            if ig_result.get("attributions_num") is not None:
                                attr_path = save_dir / f"{_safe_name(model_name)}_{key}_ig_num_attributions.npy"
                                np.save(attr_path, ig_result.get("attributions_num"))
                            if ig_result.get("attributions_geo") is not None:
                                attr_path = save_dir / f"{_safe_name(model_name)}_{key}_ig_geo_attributions.npy"
                                np.save(attr_path, ig_result.get("attributions_geo"))
                except Exception as exc:
                    print(f"[Explain] integrated gradients failed for {model_name}/{key}: {exc}")
                    continue


def explain_from_config(args: argparse.Namespace) -> None:
    script_dir = Path(__file__).resolve().parent
    config_path = resolve_config_path(args.config_json, script_dir)
    cfg = load_config_json(
        config_path,
        required_keys=["data_dir", "model_list", "model_categories", "target", "weight"],
    )
    cfg = normalize_config_paths(cfg, config_path)

    set_env(cfg.get("env", {}))

    data_dir = Path(cfg["data_dir"])
    data_dir.mkdir(parents=True, exist_ok=True)

    output_dir = args.output_dir or cfg.get("output_dir")
    if isinstance(output_dir, str) and output_dir.strip():
        resolved = resolve_path(output_dir, config_path.parent)
        if resolved is not None:
            output_dir = str(resolved)

    prop_test = cfg.get("prop_test", 0.25)
    rand_seed = cfg.get("rand_seed", 13)

    explain_cfg = dict(cfg.get("explain") or {})

    model_keys = args.model_keys or explain_cfg.get("model_keys") or ["xgb"]
    if "all" in model_keys:
        model_keys = ["glm", "xgb", "resn", "ft", "gnn"]
    model_keys = dedupe_preserve_order([str(x) for x in model_keys])

    method_list = args.methods or explain_cfg.get("methods") or ["permutation"]
    methods = _normalize_methods([str(x) for x in method_list])

    on_train = bool(args.on_train or explain_cfg.get("on_train", False))

    model_names = build_model_names(cfg["model_list"], cfg["model_categories"])
    if not model_names:
        raise ValueError("No model names generated from model_list/model_categories.")

    save_dir_raw = args.save_dir or explain_cfg.get("save_dir")
    if save_dir_raw:
        resolved = resolve_path(str(save_dir_raw), config_path.parent)
        save_root = resolved if resolved is not None else Path(str(save_dir_raw))
    else:
        save_root = None

    for model_name in model_names:
        train_path = _resolve_path_value(
            explain_cfg.get("train_path"),
            model_name=model_name,
            base_dir=config_path.parent,
            data_dir=data_dir,
        )
        if train_path is None:
            train_path = data_dir / f"{model_name}.csv"
        if not train_path.exists():
            raise FileNotFoundError(f"Missing training dataset: {train_path}")

        validation_override = args.eval_path or explain_cfg.get("validation_path") or explain_cfg.get("eval_path")
        validation_path = _resolve_path_value(
            validation_override,
            model_name=model_name,
            base_dir=config_path.parent,
            data_dir=data_dir,
        )

        raw = _load_dataset(train_path)
        if validation_path is not None:
            if not validation_path.exists():
                raise FileNotFoundError(f"Missing validation dataset: {validation_path}")
            train_df = raw
            test_df = _load_dataset(validation_path)
        else:
            if float(prop_test) <= 0:
                train_df = raw
                test_df = raw.copy()
            else:
                train_df, test_df = train_test_split(
                    raw, test_size=prop_test, random_state=rand_seed
                )

        binary_target = cfg.get("binary_target") or cfg.get("binary_resp_nme")
        feature_list = cfg.get("feature_list")
        categorical_features = cfg.get("categorical_features")

        model = ropt.BayesOptModel(
            train_df,
            test_df,
            model_name,
            cfg["target"],
            cfg["weight"],
            feature_list,
            binary_resp_nme=binary_target,
            cate_list=categorical_features,
            prop_test=prop_test,
            rand_seed=rand_seed,
            epochs=int(cfg.get("epochs", 50)),
            use_gpu=bool(cfg.get("use_gpu", True)),
            output_dir=output_dir,
            xgb_max_depth_max=int(cfg.get("xgb_max_depth_max", 25)),
            xgb_n_estimators_max=int(cfg.get("xgb_n_estimators_max", 500)),
            resn_weight_decay=cfg.get("resn_weight_decay"),
            final_ensemble=bool(cfg.get("final_ensemble", False)),
            final_ensemble_k=int(cfg.get("final_ensemble_k", 3)),
            final_refit=bool(cfg.get("final_refit", True)),
            optuna_storage=cfg.get("optuna_storage"),
            optuna_study_prefix=cfg.get("optuna_study_prefix"),
            best_params_files=cfg.get("best_params_files"),
            gnn_use_approx_knn=cfg.get("gnn_use_approx_knn", True),
            gnn_approx_knn_threshold=cfg.get("gnn_approx_knn_threshold", 50000),
            gnn_graph_cache=cfg.get("gnn_graph_cache"),
            gnn_max_gpu_knn_nodes=cfg.get("gnn_max_gpu_knn_nodes", 200000),
            gnn_knn_gpu_mem_ratio=cfg.get("gnn_knn_gpu_mem_ratio", 0.9),
            gnn_knn_gpu_mem_overhead=cfg.get("gnn_knn_gpu_mem_overhead", 2.0),
            ft_role=str(cfg.get("ft_role", "model")),
            ft_feature_prefix=str(cfg.get("ft_feature_prefix", "ft_emb")),
            ft_num_numeric_tokens=cfg.get("ft_num_numeric_tokens"),
            infer_categorical_max_unique=int(cfg.get("infer_categorical_max_unique", 50)),
            infer_categorical_max_ratio=float(cfg.get("infer_categorical_max_ratio", 0.05)),
            reuse_best_params=bool(cfg.get("reuse_best_params", False)),
        )

        model_dir_override = _resolve_path_value(
            explain_cfg.get("model_dir"),
            model_name=model_name,
            base_dir=config_path.parent,
            data_dir=None,
        )
        if model_dir_override is not None:
            model.output_manager.model_dir = model_dir_override
        result_dir_override = _resolve_path_value(
            explain_cfg.get("result_dir") or explain_cfg.get("results_dir"),
            model_name=model_name,
            base_dir=config_path.parent,
            data_dir=None,
        )
        if result_dir_override is not None:
            model.output_manager.result_dir = result_dir_override
        plot_dir_override = _resolve_path_value(
            explain_cfg.get("plot_dir"),
            model_name=model_name,
            base_dir=config_path.parent,
            data_dir=None,
        )
        if plot_dir_override is not None:
            model.output_manager.plot_dir = plot_dir_override

        if save_root is None:
            save_dir = Path(model.output_manager.result_dir) / "explain"
        else:
            save_dir = Path(save_root)
        save_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n=== Explain model {model_name} ===")
        _explain_for_model(
            model,
            model_name=model_name,
            model_keys=model_keys,
            methods=methods,
            on_train=on_train,
            save_dir=save_dir,
            explain_cfg=explain_cfg,
        )


def main() -> None:
    args = _parse_args()
    explain_from_config(args)


if __name__ == "__main__":
    main()
