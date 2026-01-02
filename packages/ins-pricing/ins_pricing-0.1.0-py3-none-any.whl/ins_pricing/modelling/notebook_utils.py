from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, cast


def _find_ins_pricing_dir(cwd: Optional[Path] = None) -> Path:
    cwd = (cwd or Path().resolve()).resolve()
    candidates = [cwd / "ins_pricing", cwd, cwd.parent / "ins_pricing"]
    for cand in candidates:
        if (cand / "modelling" / "BayesOpt_entry.py").exists() and (cand / "modelling" / "watchdog_run.py").exists():
            return cand
    raise FileNotFoundError(
        "Cannot locate ins_pricing directory (expected modelling/BayesOpt_entry.py and modelling/watchdog_run.py). "
        f"cwd={cwd}"
    )


def _stringify_cmd(cmd: Sequence[object]) -> List[str]:
    return [str(x) for x in cmd]


def build_bayesopt_entry_cmd(
    config_json: str | Path,
    model_keys: Sequence[str],
    *,
    nproc_per_node: int = 1,
    standalone: bool = True,
    entry_script: str | Path = "BayesOpt_entry.py",
    extra_args: Optional[Sequence[str]] = None,
) -> List[str]:
    """构造运行 BayesOpt_entry.py 的命令（可选 torchrun/DDP）。"""
    pkg_dir = _find_ins_pricing_dir()
    entry_script_path = Path(entry_script)
    if entry_script_path.is_absolute():
        entry_path = entry_script_path.resolve()
    else:
        candidate = pkg_dir / "modelling" / entry_script_path
        entry_path = candidate.resolve() if candidate.exists() else (pkg_dir / entry_script_path).resolve()
    config_path = Path(config_json)
    if not config_path.is_absolute():
        config_path = (pkg_dir / config_path).resolve() if (pkg_dir / config_path).exists() else config_path.resolve()

    cmd: List[object]
    if int(nproc_per_node) > 1:
        cmd = [
            sys.executable,
            "-m",
            "torch.distributed.run",
            *(["--standalone"] if standalone else []),
            f"--nproc_per_node={int(nproc_per_node)}",
            str(entry_path),
        ]
    else:
        cmd = [sys.executable, str(entry_path)]

    cmd += ["--config-json", str(config_path), "--model-keys", *list(model_keys)]
    if extra_args:
        cmd += list(extra_args)
    return _stringify_cmd(cmd)


def build_incremental_cmd(
    config_json: str | Path,
    *,
    entry_script: str | Path = "BayesOpt_incremental.py",
    extra_args: Optional[Sequence[str]] = None,
) -> List[str]:
    """构造运行 BayesOpt_incremental.py 的命令。"""
    pkg_dir = _find_ins_pricing_dir()
    entry_script_path = Path(entry_script)
    if entry_script_path.is_absolute():
        entry_path = entry_script_path.resolve()
    else:
        candidate = pkg_dir / "modelling" / entry_script_path
        entry_path = candidate.resolve() if candidate.exists() else (pkg_dir / entry_script_path).resolve()
    config_path = Path(config_json)
    if not config_path.is_absolute():
        config_path = (pkg_dir / config_path).resolve() if (pkg_dir / config_path).exists() else config_path.resolve()

    cmd: List[object] = [sys.executable, str(entry_path), "--config-json", str(config_path)]
    if extra_args:
        cmd += list(extra_args)
    return _stringify_cmd(cmd)


def build_explain_cmd(
    config_json: str | Path,
    *,
    entry_script: str | Path = "Explain_entry.py",
    extra_args: Optional[Sequence[str]] = None,
) -> List[str]:
    """构造运行 Explain_entry.py 的命令。"""
    pkg_dir = _find_ins_pricing_dir()
    entry_script_path = Path(entry_script)
    if entry_script_path.is_absolute():
        entry_path = entry_script_path.resolve()
    else:
        candidate = pkg_dir / "modelling" / entry_script_path
        entry_path = candidate.resolve() if candidate.exists() else (pkg_dir / entry_script_path).resolve()
    config_path = Path(config_json)
    if not config_path.is_absolute():
        config_path = (pkg_dir / config_path).resolve() if (pkg_dir / config_path).exists() else config_path.resolve()

    cmd: List[object] = [sys.executable, str(entry_path), "--config-json", str(config_path)]
    if extra_args:
        cmd += list(extra_args)
    return _stringify_cmd(cmd)


def wrap_with_watchdog(
    cmd: Sequence[str],
    *,
    idle_seconds: int = 7200,
    max_restarts: int = 50,
    restart_delay_seconds: int = 10,
    stop_on_nonzero_exit: bool = True,
    watchdog_script: str | Path = "watchdog_run.py",
) -> List[str]:
    """用 watchdog 包一层命令：超过 idle_seconds 无输出则自动杀进程树并重启。"""
    pkg_dir = _find_ins_pricing_dir()
    watchdog_script_path = Path(watchdog_script)
    if watchdog_script_path.is_absolute():
        watchdog_path = watchdog_script_path.resolve()
    else:
        candidate = pkg_dir / "modelling" / watchdog_script_path
        watchdog_path = candidate.resolve() if candidate.exists() else (pkg_dir / watchdog_script_path).resolve()
    wd_cmd: List[object] = [
        sys.executable,
        str(watchdog_path),
        "--idle-seconds",
        str(int(idle_seconds)),
        "--max-restarts",
        str(int(max_restarts)),
        "--restart-delay-seconds",
        str(int(restart_delay_seconds)),
    ]
    if stop_on_nonzero_exit:
        wd_cmd.append("--stop-on-nonzero-exit")
    wd_cmd.append("--")
    wd_cmd.extend(list(cmd))
    return _stringify_cmd(wd_cmd)


def run(cmd: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess:
    """在 notebook 中运行外部命令（同步等待）。"""
    return subprocess.run(list(cmd), check=check)


def run_bayesopt_entry(
    *,
    config_json: str | Path,
    model_keys: Sequence[str],
    max_evals: int = 50,
    plot_curves: bool = True,
    ft_role: Optional[str] = None,
    nproc_per_node: int = 1,
    use_watchdog: bool = False,
    idle_seconds: int = 7200,
    max_restarts: int = 50,
    restart_delay_seconds: int = 10,
    extra_args: Optional[Sequence[str]] = None,
) -> subprocess.CompletedProcess:
    """便捷封装：构造并运行 BayesOpt_entry（可选 torchrun + watchdog）。"""
    args: List[str] = ["--max-evals", str(int(max_evals))]
    if plot_curves:
        args.append("--plot-curves")
    if ft_role:
        args += ["--ft-role", str(ft_role)]
    if extra_args:
        args += list(extra_args)

    cmd = build_bayesopt_entry_cmd(
        config_json=config_json,
        model_keys=model_keys,
        nproc_per_node=nproc_per_node,
        extra_args=args,
    )
    if use_watchdog:
        cmd = wrap_with_watchdog(
            cmd,
            idle_seconds=idle_seconds,
            max_restarts=max_restarts,
            restart_delay_seconds=restart_delay_seconds,
        )
    return run(cmd, check=True)


def run_from_config(config_json: str | Path) -> subprocess.CompletedProcess:
    """Notebook 统一入口：只修改 config 文件即可切换不同运行方式。

    约定：config.json 可选增加一个 `runner` 字段，用于 notebook 执行控制：
    - runner.mode: "entry"（默认）或 "incremental"
    - runner.nproc_per_node: >1 则使用 torchrun/DDP（仅 entry）
    - runner.model_keys: 需要运行的模型列表（仅 entry）
    - runner.max_evals / runner.plot_curves / runner.ft_role（仅 entry，可覆盖 config 内同名字段）
    - runner.use_watchdog / runner.idle_seconds / runner.max_restarts / runner.restart_delay_seconds
    - runner.incremental_args: List[str]（仅 incremental，等价于直接传给 BayesOpt_incremental.py 的额外参数）
    """
    pkg_dir = _find_ins_pricing_dir()
    config_path = Path(config_json)
    if not config_path.is_absolute():
        config_path = (pkg_dir / config_path).resolve() if (pkg_dir / config_path).exists() else config_path.resolve()
    raw = json.loads(config_path.read_text(encoding="utf-8", errors="replace"))
    runner = cast(dict, raw.get("runner") or {})

    mode = str(runner.get("mode") or "entry").strip().lower()
    use_watchdog = bool(runner.get("use_watchdog", False))
    idle_seconds = int(runner.get("idle_seconds", 7200))
    max_restarts = int(runner.get("max_restarts", 50))
    restart_delay_seconds = int(runner.get("restart_delay_seconds", 10))

    if mode == "incremental":
        inc_args = runner.get("incremental_args") or []
        if not isinstance(inc_args, list):
            raise ValueError("config.runner.incremental_args must be a list of strings.")
        cmd = build_incremental_cmd(config_path, extra_args=[str(x) for x in inc_args])
        if use_watchdog:
            cmd = wrap_with_watchdog(
                cmd,
                idle_seconds=idle_seconds,
                max_restarts=max_restarts,
                restart_delay_seconds=restart_delay_seconds,
            )
        return run(cmd, check=True)

    if mode == "explain":
        exp_args = runner.get("explain_args") or []
        if not isinstance(exp_args, list):
            raise ValueError("config.runner.explain_args must be a list of strings.")
        cmd = build_explain_cmd(config_path, extra_args=[str(x) for x in exp_args])
        if use_watchdog:
            cmd = wrap_with_watchdog(
                cmd,
                idle_seconds=idle_seconds,
                max_restarts=max_restarts,
                restart_delay_seconds=restart_delay_seconds,
            )
        return run(cmd, check=True)

    if mode != "entry":
        raise ValueError(
            f"Unsupported runner.mode={mode!r}, expected 'entry', 'incremental', or 'explain'."
        )

    model_keys = runner.get("model_keys")
    if not model_keys:
        model_keys = raw.get("model_keys")
    if not model_keys:
        model_keys = ["ft"]
    if not isinstance(model_keys, list):
        raise ValueError("runner.model_keys must be a list of strings.")

    nproc_per_node = int(runner.get("nproc_per_node", 1))
    max_evals = int(runner.get("max_evals", raw.get("max_evals", 50)))
    plot_curves = bool(runner.get("plot_curves", raw.get("plot_curves", True)))
    ft_role = runner.get("ft_role", None)
    if ft_role is None:
        ft_role = raw.get("ft_role")

    cmd = build_bayesopt_entry_cmd(
        config_path,
        model_keys=[str(x) for x in model_keys],
        nproc_per_node=nproc_per_node,
        extra_args=[
            "--max-evals",
            str(max_evals),
            *(["--plot-curves"] if plot_curves else []),
            *(["--ft-role", str(ft_role)] if ft_role else []),
        ],
    )

    if use_watchdog:
        cmd = wrap_with_watchdog(
            cmd,
            idle_seconds=idle_seconds,
            max_restarts=max_restarts,
            restart_delay_seconds=restart_delay_seconds,
        )
    return run(cmd, check=True)
