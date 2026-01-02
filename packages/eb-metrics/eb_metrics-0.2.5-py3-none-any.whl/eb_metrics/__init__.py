"""
`eb_metrics` — core metric library for the Electric Barometer ecosystem.

This package exposes a clean, stable public API for:

- Asymmetric cost-weighted loss metrics (e.g., Cost-Weighted Service Loss, CWSL)
- Classical regression metrics (MAE, MSE, RMSE, MAPE, WMAPE, etc.)
- Service-level and readiness metrics (NSL, UD, HR@τ, FRS)

Conceptual definitions and interpretation are documented in the companion
research repository (`eb-papers`).

Notes
-----
The recommended import path is either:

- package root (convenience): ``from eb_metrics import cwsl, nsl, frs``
- submodules (explicit): ``from eb_metrics.metrics.loss import cwsl``

Internal helpers live in private modules (prefixed with "_") and are not part of
the public API.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .metrics.loss import cwsl
from .metrics.regression import (
    mae,
    mape,
    mase,
    medae,
    mse,
    msle,
    rmse,
    rmsle,
    smape,
    wmape,
)
from .metrics.service import cwsl_sensitivity, frs, hr_at_tau, nsl, ud


def _resolve_version() -> str:
    """
    Resolve the installed package version.

    Returns
    -------
    str
        Installed version string. If the package is not installed (e.g., running
        from source without installation), returns ``"0.0.0"``.
    """
    try:
        # Must match the distribution name in pyproject.toml ([project].name)
        return version("eb-metrics")
    except PackageNotFoundError:
        return "0.0.0"


__version__ = _resolve_version()


__all__ = [
    "__version__",
    "cwsl",
    "cwsl_sensitivity",
    "frs",
    "hr_at_tau",
    "mae",
    "mape",
    "mase",
    "medae",
    "mse",
    "msle",
    "nsl",
    "rmse",
    "rmsle",
    "smape",
    "ud",
    "wmape",
]
