"""
CLI entry point generated from BayesOpt_AutoPricing.ipynb so the workflow can
run non‑interactively (e.g., via torchrun).

Example:
    python -m torch.distributed.run --standalone --nproc_per_node=2 \\
        ins_pricing/modelling/BayesOpt_entry.py \\
        --config-json ins_pricing/modelling/demo/config_template.json \\
        --model-keys ft --max-evals 50 --use-ft-ddp
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict, List

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

import matplotlib

if os.name != "nt" and not os.environ.get("DISPLAY") and not os.environ.get("MPLBACKEND"):
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from .plotting.diagnostics import plot_loss_curve as plot_loss_curve_common
except Exception:  # pragma: no cover
    try:
        from ins_pricing.plotting.diagnostics import plot_loss_curve as plot_loss_curve_common
    except Exception:  # pragma: no cover
        plot_loss_curve_common = None

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch trainer generated from BayesOpt_AutoPricing notebook."
    )
    parser.add_argument(
        "--config-json",
        required=True,
        help="Path to the JSON config describing datasets and feature columns.",
    )
    parser.add_argument(
        "--model-keys",
        nargs="+",
        default=["ft"],
        choices=["glm", "xgb", "resn", "ft", "gnn", "all"],
        help="Space-separated list of trainers to run (e.g., --model-keys glm xgb). Include 'all' to run every trainer.",
    )
    parser.add_argument(
        "--stack-model-keys",
        nargs="+",
        default=None,
        choices=["glm", "xgb", "resn", "ft", "gnn", "all"],
        help=(
            "Only used when ft_role != 'model' (FT runs as feature generator). "
            "When provided (or when config defines stack_model_keys), these trainers run after FT features "
            "are generated. Use 'all' to run every non-FT trainer."
        ),
    )
    parser.add_argument(
        "--max-evals",
        type=int,
        default=50,
        help="Optuna trial count per dataset.",
    )
    parser.add_argument(
        "--use-resn-ddp",
        action="store_true",
        help="Force ResNet trainer to use DistributedDataParallel.",
    )
    parser.add_argument(
        "--use-ft-ddp",
        action="store_true",
        help="Force FT-Transformer trainer to use DistributedDataParallel.",
    )
    parser.add_argument(
        "--use-resn-dp",
        action="store_true",
        help="Enable ResNet DataParallel fall-back regardless of config.",
    )
    parser.add_argument(
        "--use-ft-dp",
        action="store_true",
        help="Enable FT-Transformer DataParallel fall-back regardless of config.",
    )
    parser.add_argument(
        "--use-gnn-dp",
        action="store_true",
        help="Enable GNN DataParallel fall-back regardless of config.",
    )
    parser.add_argument(
        "--use-gnn-ddp",
        action="store_true",
        help="Force GNN trainer to use DistributedDataParallel.",
    )
    parser.add_argument(
        "--gnn-no-ann",
        action="store_true",
        help="Disable approximate k-NN for GNN graph construction and use exact search.",
    )
    parser.add_argument(
        "--gnn-ann-threshold",
        type=int,
        default=None,
        help="Row threshold above which approximate k-NN is preferred (overrides config).",
    )
    parser.add_argument(
        "--gnn-graph-cache",
        default=None,
        help="Optional path to persist/load cached adjacency matrix for GNN.",
    )
    parser.add_argument(
        "--gnn-max-gpu-nodes",
        type=int,
        default=None,
        help="Overrides the maximum node count allowed for GPU k-NN graph construction.",
    )
    parser.add_argument(
        "--gnn-gpu-mem-ratio",
        type=float,
        default=None,
        help="Overrides the fraction of free GPU memory the k-NN builder may consume.",
    )
    parser.add_argument(
        "--gnn-gpu-mem-overhead",
        type=float,
        default=None,
        help="Overrides the temporary GPU memory overhead multiplier for k-NN estimation.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Override output root for models/results/plots.",
    )
    parser.add_argument(
        "--plot-curves",
        action="store_true",
        help="Enable lift/diagnostic plots after training (config file may also request plotting).",
    )
    parser.add_argument(
        "--ft-as-feature",
        action="store_true",
        help="Alias for --ft-role embedding (keep tuning, export embeddings; skip FT plots/SHAP).",
    )
    parser.add_argument(
        "--ft-role",
        default=None,
        choices=["model", "embedding", "unsupervised_embedding"],
        help="How to use FT: model (default), embedding (export pooling embeddings), or unsupervised_embedding.",
    )
    parser.add_argument(
        "--ft-feature-prefix",
        default="ft_feat",
        help="Prefix used for generated FT features (columns: pred_<prefix>_0.. or pred_<prefix>).",
    )
    parser.add_argument(
        "--reuse-best-params",
        action="store_true",
        help="Skip Optuna and reuse best_params saved in Results/versions or bestparams CSV when available.",
    )
    return parser.parse_args()


def _plot_curves_for_model(model: ropt.BayesOptModel, trained_keys: List[str], cfg: Dict) -> None:
    plot_cfg = cfg.get("plot", {})
    legacy_lift_flags = {
        "glm": cfg.get("plot_lift_glm", False),
        "xgb": cfg.get("plot_lift_xgb", False),
        "resn": cfg.get("plot_lift_resn", False),
        "ft": cfg.get("plot_lift_ft", False),
    }
    plot_enabled = plot_cfg.get("enable", any(legacy_lift_flags.values()))
    if not plot_enabled:
        return

    n_bins = int(plot_cfg.get("n_bins", 10))
    oneway_enabled = plot_cfg.get("oneway", True)

    available_models = dedupe_preserve_order(
        [m for m in trained_keys if m in PLOT_MODEL_LABELS]
    )

    if oneway_enabled:
        model.plot_oneway(n_bins=n_bins)

    if not available_models:
        return

    lift_models = plot_cfg.get("lift_models")
    if lift_models is None:
        lift_models = [
            m for m, enabled in legacy_lift_flags.items() if enabled]
        if not lift_models:
            lift_models = available_models
    lift_models = dedupe_preserve_order(
        [m for m in lift_models if m in available_models]
    )

    for model_key in lift_models:
        label, pred_nme = PLOT_MODEL_LABELS[model_key]
        model.plot_lift(model_label=label, pred_nme=pred_nme, n_bins=n_bins)

    if not plot_cfg.get("double_lift", True) or len(available_models) < 2:
        return

    raw_pairs = plot_cfg.get("double_lift_pairs")
    if raw_pairs:
        pairs = [
            (a, b)
            for a, b in parse_model_pairs(raw_pairs)
            if a in available_models and b in available_models and a != b
        ]
    else:
        pairs = [(a, b) for i, a in enumerate(available_models) for b in available_models[i + 1 :]]

    for first, second in pairs:
        model.plot_dlift([first, second], n_bins=n_bins)


def _plot_loss_curve_for_trainer(model_name: str, trainer) -> None:
    model_obj = getattr(trainer, "model", None)
    history = None
    if model_obj is not None:
        history = getattr(model_obj, "training_history", None)
    if not history:
        history = getattr(trainer, "training_history", None)
    if not history:
        return
    train_hist = list(history.get("train") or [])
    val_hist = list(history.get("val") or [])
    if not train_hist and not val_hist:
        return
    try:
        plot_dir = trainer.output.plot_path(
            f"loss_{model_name}_{trainer.model_name_prefix}.png"
        )
    except Exception:
        default_dir = Path("plot")
        default_dir.mkdir(parents=True, exist_ok=True)
        plot_dir = str(
            default_dir / f"loss_{model_name}_{trainer.model_name_prefix}.png")
    if plot_loss_curve_common is not None:
        plot_loss_curve_common(
            history=history,
            title=f"{trainer.model_name_prefix} Loss Curve ({model_name})",
            save_path=plot_dir,
            show=False,
        )
    else:
        epochs = range(1, max(len(train_hist), len(val_hist)) + 1)
        fig, ax = plt.subplots(figsize=(8, 4))
        if train_hist:
            ax.plot(range(1, len(train_hist) + 1),
                    train_hist, label="Train Loss", color="tab:blue")
        if val_hist:
            ax.plot(range(1, len(val_hist) + 1),
                    val_hist, label="Validation Loss", color="tab:orange")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Weighted Loss")
        ax.set_title(
            f"{trainer.model_name_prefix} Loss Curve ({model_name})")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend()
        plt.tight_layout()
        plt.savefig(plot_dir, dpi=300)
        plt.close(fig)
    print(
        f"[Plot] Saved loss curve for {model_name}/{trainer.label} -> {plot_dir}")


def train_from_config(args: argparse.Namespace) -> None:
    script_dir = Path(__file__).resolve().parent
    config_path = resolve_config_path(args.config_json, script_dir)
    cfg = load_config_json(
        config_path,
        required_keys=["data_dir", "model_list", "model_categories", "target", "weight"],
    )
    cfg = normalize_config_paths(cfg, config_path)

    set_env(cfg.get("env", {}))
    plot_requested = bool(args.plot_curves or cfg.get("plot_curves", False))

    def _safe_int_env(key: str, default: int) -> int:
        try:
            return int(os.environ.get(key, default))
        except (TypeError, ValueError):
            return default

    dist_world_size = _safe_int_env("WORLD_SIZE", 1)
    dist_rank = _safe_int_env("RANK", 0)
    dist_active = dist_world_size > 1

    data_dir = Path(cfg["data_dir"])
    data_dir.mkdir(parents=True, exist_ok=True)

    prop_test = cfg.get("prop_test", 0.25)
    rand_seed = cfg.get("rand_seed", 13)
    epochs = cfg.get("epochs", 50)
    output_dir = args.output_dir or cfg.get("output_dir")
    if isinstance(output_dir, str) and output_dir.strip():
        resolved = resolve_path(output_dir, config_path.parent)
        if resolved is not None:
            output_dir = str(resolved)
    reuse_best_params = bool(args.reuse_best_params or cfg.get("reuse_best_params", False))
    xgb_max_depth_max = int(cfg.get("xgb_max_depth_max", 25))
    xgb_n_estimators_max = int(cfg.get("xgb_n_estimators_max", 500))
    optuna_storage = cfg.get("optuna_storage")
    optuna_study_prefix = cfg.get("optuna_study_prefix")
    best_params_files = cfg.get("best_params_files")

    model_names = build_model_names(
        cfg["model_list"], cfg["model_categories"])
    if not model_names:
        raise ValueError(
            "No model names generated from model_list/model_categories.")

    results: Dict[str, ropt.BayesOptModel] = {}
    trained_keys_by_model: Dict[str, List[str]] = {}

    for model_name in model_names:
        # Per-dataset training loop: load data, split train/test, and train requested models.
        csv_path = data_dir / f"{model_name}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing dataset: {csv_path}")

        print(f"\n=== Processing model {model_name} ===")
        raw = pd.read_csv(csv_path, low_memory=False)
        raw = raw.copy()
        for col in raw.columns:
            s = raw[col]
            if pd.api.types.is_numeric_dtype(s):
                raw[col] = pd.to_numeric(s, errors="coerce").fillna(0)
            else:
                raw[col] = s.astype("object").fillna("<NA>")

        train_df, test_df = train_test_split(
            raw, test_size=prop_test, random_state=rand_seed
        )

        use_resn_dp = args.use_resn_dp or cfg.get(
            "use_resn_data_parallel", False)
        use_ft_dp = args.use_ft_dp or cfg.get("use_ft_data_parallel", True)
        use_resn_ddp = args.use_resn_ddp or cfg.get("use_resn_ddp", False)
        use_ft_ddp = args.use_ft_ddp or cfg.get("use_ft_ddp", False)
        use_gnn_dp = args.use_gnn_dp or cfg.get("use_gnn_data_parallel", False)
        use_gnn_ddp = args.use_gnn_ddp or cfg.get("use_gnn_ddp", False)
        gnn_use_ann = cfg.get("gnn_use_approx_knn", True)
        if args.gnn_no_ann:
            gnn_use_ann = False
        gnn_threshold = args.gnn_ann_threshold if args.gnn_ann_threshold is not None else cfg.get(
            "gnn_approx_knn_threshold", 50000)
        gnn_graph_cache = args.gnn_graph_cache or cfg.get("gnn_graph_cache")
        if isinstance(gnn_graph_cache, str) and gnn_graph_cache.strip():
            resolved_cache = resolve_path(gnn_graph_cache, config_path.parent)
            if resolved_cache is not None:
                gnn_graph_cache = str(resolved_cache)
        gnn_max_gpu_nodes = args.gnn_max_gpu_nodes if args.gnn_max_gpu_nodes is not None else cfg.get(
            "gnn_max_gpu_knn_nodes", 200000)
        gnn_gpu_mem_ratio = args.gnn_gpu_mem_ratio if args.gnn_gpu_mem_ratio is not None else cfg.get(
            "gnn_knn_gpu_mem_ratio", 0.9)
        gnn_gpu_mem_overhead = args.gnn_gpu_mem_overhead if args.gnn_gpu_mem_overhead is not None else cfg.get(
            "gnn_knn_gpu_mem_overhead", 2.0)

        binary_target = cfg.get("binary_target") or cfg.get("binary_resp_nme")
        feature_list = cfg.get("feature_list")
        categorical_features = cfg.get("categorical_features")

        ft_role = args.ft_role or cfg.get("ft_role", "model")
        if args.ft_as_feature and args.ft_role is None:
            # Keep legacy behavior as a convenience alias only when the config
            # didn't already request a non-default FT role.
            if str(cfg.get("ft_role", "model")) == "model":
                ft_role = "embedding"
        ft_feature_prefix = str(cfg.get("ft_feature_prefix", args.ft_feature_prefix))
        ft_num_numeric_tokens = cfg.get("ft_num_numeric_tokens")

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
            epochs=epochs,
            use_resn_data_parallel=use_resn_dp,
            use_ft_data_parallel=use_ft_dp,
            use_resn_ddp=use_resn_ddp,
            use_ft_ddp=use_ft_ddp,
            use_gnn_data_parallel=use_gnn_dp,
            use_gnn_ddp=use_gnn_ddp,
            output_dir=output_dir,
            xgb_max_depth_max=xgb_max_depth_max,
            xgb_n_estimators_max=xgb_n_estimators_max,
            resn_weight_decay=cfg.get("resn_weight_decay"),
            final_ensemble=bool(cfg.get("final_ensemble", False)),
            final_ensemble_k=int(cfg.get("final_ensemble_k", 3)),
            final_refit=bool(cfg.get("final_refit", True)),
            optuna_storage=optuna_storage,
            optuna_study_prefix=optuna_study_prefix,
            best_params_files=best_params_files,
            gnn_use_approx_knn=gnn_use_ann,
            gnn_approx_knn_threshold=gnn_threshold,
            gnn_graph_cache=gnn_graph_cache,
            gnn_max_gpu_knn_nodes=gnn_max_gpu_nodes,
            gnn_knn_gpu_mem_ratio=gnn_gpu_mem_ratio,
            gnn_knn_gpu_mem_overhead=gnn_gpu_mem_overhead,
            ft_role=ft_role,
            ft_feature_prefix=ft_feature_prefix,
            ft_num_numeric_tokens=ft_num_numeric_tokens,
            infer_categorical_max_unique=int(cfg.get("infer_categorical_max_unique", 50)),
            infer_categorical_max_ratio=float(cfg.get("infer_categorical_max_ratio", 0.05)),
            reuse_best_params=reuse_best_params,
        )

        if "all" in args.model_keys:
            requested_keys = ["glm", "xgb", "resn", "ft", "gnn"]
        else:
            requested_keys = args.model_keys
        requested_keys = dedupe_preserve_order(requested_keys)

        if ft_role != "model":
            requested_keys = [k for k in requested_keys if k != "ft"]
            if not requested_keys:
                stack_keys = args.stack_model_keys or cfg.get("stack_model_keys")
                if stack_keys:
                    if "all" in stack_keys:
                        requested_keys = ["glm", "xgb", "resn", "gnn"]
                    else:
                        requested_keys = [k for k in stack_keys if k != "ft"]
                    requested_keys = dedupe_preserve_order(requested_keys)
            if dist_active:
                ft_trainer = model.trainers.get("ft")
                if ft_trainer is None:
                    raise ValueError("FT trainer is not available.")
                ft_trainer_uses_ddp = bool(
                    getattr(ft_trainer, "enable_distributed_optuna", False))
                if not ft_trainer_uses_ddp:
                    raise ValueError(
                        "FT embedding under torchrun requires enabling FT DDP (use --use-ft-ddp or set use_ft_ddp=true)."
                    )
        missing = [key for key in requested_keys if key not in model.trainers]
        if missing:
            raise ValueError(
                f"Trainer(s) {missing} not available for {model_name}")

        executed_keys: List[str] = []
        if ft_role != "model":
            print(
                f"Optimizing ft as {ft_role} for {model_name} (max_evals={args.max_evals})")
            model.optimize_model("ft", max_evals=args.max_evals)
            model.trainers["ft"].save()
            if getattr(ropt, "torch", None) is not None and ropt.torch.cuda.is_available():
                ropt.free_cuda()
        for key in requested_keys:
            trainer = model.trainers[key]
            trainer_uses_ddp = bool(
                getattr(trainer, "enable_distributed_optuna", False))
            should_run = True
            if dist_active and not trainer_uses_ddp:
                should_run = dist_rank == 0
                if not should_run:
                    print(
                        f"[Rank {dist_rank}] Skip {model_name}/{key} because trainer is not DDP-enabled."
                    )
                    continue

            print(
                f"Optimizing {key} for {model_name} (max_evals={args.max_evals})")
            model.optimize_model(key, max_evals=args.max_evals)
            model.trainers[key].save()
            _plot_loss_curve_for_trainer(model_name, model.trainers[key])
            if key in PYTORCH_TRAINERS:
                ropt.free_cuda()
            executed_keys.append(key)

        if not executed_keys:
            continue

        results[model_name] = model
        trained_keys_by_model[model_name] = executed_keys

    if not plot_requested:
        return

    for name, model in results.items():
        _plot_curves_for_model(
            model,
            trained_keys_by_model.get(name, []),
            cfg,
        )


def main() -> None:
    args = _parse_args()
    train_from_config(args)


if __name__ == "__main__":
    main()
