from __future__ import annotations

from importlib import import_module

# Keep imports lazy to avoid hard dependencies when only using lightweight modules.

__all__ = [
    "BayesOptConfig",
    "BayesOptModel",
    "IOUtils",
    "TrainingUtils",
    "free_cuda",
    "bayesopt",
    "plotting",
    "explain",
]

_LAZY_ATTRS = {
    "bayesopt": "ins_pricing.modelling.bayesopt",
    "plotting": "ins_pricing.modelling.plotting",
    "explain": "ins_pricing.modelling.explain",
    "BayesOptConfig": "ins_pricing.modelling.bayesopt.core",
    "BayesOptModel": "ins_pricing.modelling.bayesopt.core",
    "IOUtils": "ins_pricing.modelling.bayesopt.utils",
    "TrainingUtils": "ins_pricing.modelling.bayesopt.utils",
    "free_cuda": "ins_pricing.modelling.bayesopt.utils",
}


def __getattr__(name: str):
    target = _LAZY_ATTRS.get(name)
    if not target:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(target)
    if name in {"bayesopt", "plotting", "explain"}:
        value = module
    else:
        value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(globals().keys()))
