"""
Public metric API for the Electric Barometer ecosystem.

The `eb_metrics.metrics` package provides a curated, stable import surface for
Electric Barometer evaluation metrics.

This package groups metrics into three main categories:

- **Asymmetric loss metrics** (`loss`)
  Cost-aware losses that encode directional operational asymmetry.

- **Service and readiness diagnostics** (`service`)
  Metrics that quantify shortfall avoidance, tolerance coverage, and readiness.

- **Classical regression metrics** (`regression`)
  Standard symmetric error metrics used for baseline comparison.

Conceptual definitions and interpretation of Electric Barometer metrics are
documented in the companion research repository (`eb-papers`). This package is
the executable reference implementation.

Notes
-----
Users are encouraged to import from `eb_metrics.metrics` or from the relevant
submodule (e.g., `eb_metrics.metrics.service`) rather than internal helpers.

Cost-ratio selection / tuning utilities (e.g., searching for an optimal
R = c_u / c_o) live in `eb-optimization`, not `eb-metrics`.

Examples
--------
Import from the package surface:

>>> from eb_metrics.metrics import cwsl, nsl, frs

Or import from a submodule:

>>> from eb_metrics.metrics.loss import cwsl
>>> from eb_metrics.metrics.service import nsl
"""

from __future__ import annotations

from .loss import cwsl
from .regression import (
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
from .service import cwsl_sensitivity, frs, hr_at_tau, nsl, ud

######################################
# Public API
######################################

__all__ = [
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
