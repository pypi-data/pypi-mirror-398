from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

try:
    from .notebook_utils import run_from_config  # type: ignore
except Exception:  # pragma: no cover
    from notebook_utils import run_from_config  # type: ignore


def run(config_json: str | Path) -> None:
    """Run explain by config.json (runner.mode=explain)."""
    run_from_config(config_json)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explain_Run: run explain by config.json (runner.mode=explain)."
    )
    parser.add_argument(
        "--config-json",
        required=True,
        help="Path to config.json (relative paths are resolved from ins_pricing/modelling/ when possible).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    args = _build_parser().parse_args(argv)
    run(args.config_json)


if __name__ == "__main__":
    main()
