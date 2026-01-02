from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


PLOT_MODEL_LABELS: Dict[str, Tuple[str, str]] = {
    "glm": ("GLM", "pred_glm"),
    "xgb": ("Xgboost", "pred_xgb"),
    "resn": ("ResNet", "pred_resn"),
    "ft": ("FTTransformer", "pred_ft"),
    "gnn": ("GNN", "pred_gnn"),
}

PYTORCH_TRAINERS = {"resn", "ft", "gnn"}


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    unique: List[str] = []
    for item in items:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


def build_model_names(prefixes: Sequence[str], suffixes: Sequence[str]) -> List[str]:
    names: List[str] = []
    for suffix in suffixes:
        names.extend(f"{prefix}_{suffix}" for prefix in prefixes)
    return names


def parse_model_pairs(raw_pairs: List) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for pair in raw_pairs:
        if isinstance(pair, (list, tuple)) and len(pair) == 2:
            pairs.append((str(pair[0]), str(pair[1])))
        elif isinstance(pair, str):
            parts = [p.strip() for p in pair.split(",") if p.strip()]
            if len(parts) == 2:
                pairs.append((parts[0], parts[1]))
    return pairs


def resolve_path(value: Optional[str], base_dir: Path) -> Optional[Path]:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    p = Path(value)
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()


def resolve_config_path(raw: str, script_dir: Path) -> Path:
    candidate = Path(raw)
    if candidate.exists():
        return candidate.resolve()
    candidate2 = (script_dir / raw)
    if candidate2.exists():
        return candidate2.resolve()
    raise FileNotFoundError(
        f"Config file not found: {raw}. Tried: {Path(raw).resolve()} and {candidate2.resolve()}"
    )


def load_config_json(path: Path, required_keys: Sequence[str]) -> Dict[str, Any]:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    missing = [key for key in required_keys if key not in cfg]
    if missing:
        raise ValueError(f"Missing required keys in {path}: {missing}")
    return cfg


def set_env(env_overrides: Dict[str, Any]) -> None:
    """Apply environment variables from config.json.

    Notes (DDP/Optuna hang debugging):
    - You can add these keys into config.json's `env` to debug distributed hangs:
      - `TORCH_DISTRIBUTED_DEBUG=DETAIL`
      - `NCCL_DEBUG=INFO`
      - `BAYESOPT_DDP_BARRIER_DEBUG=1`
      - `BAYESOPT_DDP_BARRIER_TIMEOUT=300`
      - `BAYESOPT_CUDA_SYNC=1` (optional; can slow down)
      - `BAYESOPT_CUDA_IPC_COLLECT=1` (optional; can slow down)
    - This function uses `os.environ.setdefault`, so a value already set in the
      shell will take precedence over config.json.
    """
    for key, value in (env_overrides or {}).items():
        os.environ.setdefault(str(key), str(value))


def _looks_like_url(value: str) -> bool:
    value = str(value)
    return "://" in value


def normalize_config_paths(cfg: Dict[str, Any], config_path: Path) -> Dict[str, Any]:
    """Resolve relative paths against the config.json directory.

    Fields handled:
    - data_dir / output_dir / optuna_storage / gnn_graph_cache
    - best_params_files (dict: model_key -> path)
    """
    base_dir = config_path.parent
    out = dict(cfg)

    for key in ("data_dir", "output_dir", "gnn_graph_cache"):
        if key in out and isinstance(out.get(key), str):
            resolved = resolve_path(out.get(key), base_dir)
            if resolved is not None:
                out[key] = str(resolved)

    storage = out.get("optuna_storage")
    if isinstance(storage, str) and storage.strip():
        if not _looks_like_url(storage):
            resolved = resolve_path(storage, base_dir)
            if resolved is not None:
                out["optuna_storage"] = str(resolved)

    best_files = out.get("best_params_files")
    if isinstance(best_files, dict):
        resolved_map: Dict[str, str] = {}
        for mk, path_str in best_files.items():
            if not isinstance(path_str, str):
                continue
            resolved = resolve_path(path_str, base_dir)
            resolved_map[str(mk)] = str(resolved) if resolved is not None else str(path_str)
        out["best_params_files"] = resolved_map

    return out
