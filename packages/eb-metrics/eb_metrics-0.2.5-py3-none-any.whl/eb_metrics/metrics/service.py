"""
Service-level and readiness metrics for the Electric Barometer ecosystem.

This module contains evaluation metrics that complement asymmetric loss (e.g.,
CWSL) by measuring **service behavior** and **readiness characteristics**:

- **NSL**: how often forecasts avoid shortfall (service reliability)
- **UD**: how deep shortfalls are when they occur (service severity)
- **HR@τ**: how often forecasts fall within a tolerance band (accuracy within bounds)
- **FRS**: a composite readiness score built from NSL and CWSL
- **CWSL sensitivity**: how CWSL changes under alternative cost-ratio assumptions

Operational definitions, interpretation, and motivation are documented in the
companion research repository (`eb-papers`).

Design note
-----------
- `cwsl_sensitivity` remains in **eb-metrics** because it is deterministic metric
  evaluation (a convenience wrapper around `cwsl`).
- DataFrame-oriented plumbing and tuning workflows live in **eb-optimization**.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import ArrayLike

from .._utils import _broadcast_param, _handle_sample_weight, _to_1d_array
from .loss import cwsl

__all__ = ["cwsl_sensitivity", "frs", "hr_at_tau", "nsl", "ud"]


def nsl(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    sample_weight: ArrayLike | None = None,
) -> float:
    r"""
    Compute No-Shortfall Level (NSL).

    NSL is the (optionally weighted) fraction of evaluation intervals in which
    the forecast does **not** underpredict realized demand.

    For each interval $i$, define a hit indicator:

    $$
    h_i = \mathbb{1}[\hat{y}_i \ge y_i]
    $$

    Then:

    $$
    \mathrm{NSL} = \frac{\sum_i w_i \; h_i}{\sum_i w_i}
    $$

    where $w_i$ are optional sample weights (default $w_i = 1$).
    Higher values are better, with $\mathrm{NSL} \in [0, 1]$.
    """
    y_true_arr = _to_1d_array(y_true, "y_true")
    y_pred_arr = _to_1d_array(y_pred, "y_pred")

    if y_true_arr.shape != y_pred_arr.shape:
        raise ValueError(
            "y_true and y_pred must have the same shape; "
            f"got {y_true_arr.shape} and {y_pred_arr.shape}"
        )

    if np.any(y_true_arr < 0):
        raise ValueError("y_true must be non-negative (demand cannot be negative).")
    if np.any(y_pred_arr < 0):
        raise ValueError("y_pred must be non-negative (forecast cannot be negative).")

    n = y_true_arr.shape[0]
    w = _handle_sample_weight(sample_weight, n)

    hits = (y_pred_arr >= y_true_arr).astype(float)

    total_weight = float(w.sum())
    if total_weight <= 0:
        raise ValueError(
            "NSL is undefined: total sample_weight is zero. Check your weighting scheme."
        )

    return float(np.sum(w * hits) / total_weight)


def ud(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    sample_weight: ArrayLike | None = None,
) -> float:
    r"""
    Compute Underbuild Depth (UD).

    UD measures the (optionally weighted) *average magnitude* of shortfall.
    Unlike NSL (which counts shortfalls), UD quantifies **how severe** shortfalls
    are when they occur.

    Define per-interval shortfall:

    $$
    s_i = \max(0, y_i - \hat{y}_i)
    $$

    Then:

    $$
    \mathrm{UD} = \frac{\sum_i w_i \; s_i}{\sum_i w_i}
    $$

    Higher values indicate deeper average shortfall; **lower is better**.
    """
    y_true_arr = _to_1d_array(y_true, "y_true")
    y_pred_arr = _to_1d_array(y_pred, "y_pred")

    if y_true_arr.shape != y_pred_arr.shape:
        raise ValueError(
            "y_true and y_pred must have the same shape; "
            f"got {y_true_arr.shape} and {y_pred_arr.shape}"
        )

    if np.any(y_true_arr < 0):
        raise ValueError("y_true must be non-negative (demand cannot be negative).")
    if np.any(y_pred_arr < 0):
        raise ValueError("y_pred must be non-negative (forecast cannot be negative).")

    n = y_true_arr.shape[0]
    w = _handle_sample_weight(sample_weight, n)

    shortfall = np.maximum(0.0, y_true_arr - y_pred_arr)

    total_weight = float(w.sum())
    if total_weight <= 0:
        raise ValueError(
            "UD is undefined: total sample_weight is zero. Check your weighting scheme."
        )

    return float(np.sum(w * shortfall) / total_weight)


def hr_at_tau(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    tau: float | ArrayLike,
    sample_weight: ArrayLike | None = None,
) -> float:
    r"""
    Compute Hit Rate within Tolerance (HR@τ).

    HR@τ measures the (optionally weighted) fraction of intervals whose absolute
    error falls within a tolerance band $\tau$.

    Define absolute error and hit indicator:

    $$
    \begin{aligned}
    e_i &= |y_i - \hat{y}_i| \\
    h_i &= \mathbb{1}[e_i \le \tau_i]
    \end{aligned}
    $$

    Then:

    $$
    \mathrm{HR@\tau} = \frac{\sum_i w_i \; h_i}{\sum_i w_i}
    $$
    """
    y_true_arr = _to_1d_array(y_true, "y_true")
    y_pred_arr = _to_1d_array(y_pred, "y_pred")

    if y_true_arr.shape != y_pred_arr.shape:
        raise ValueError(
            "y_true and y_pred must have the same shape; "
            f"got {y_true_arr.shape} and {y_pred_arr.shape}"
        )

    if np.any(y_true_arr < 0):
        raise ValueError("y_true must be non-negative (demand cannot be negative).")
    if np.any(y_pred_arr < 0):
        raise ValueError("y_pred must be non-negative (forecast cannot be negative).")

    n = y_true_arr.shape[0]
    w = _handle_sample_weight(sample_weight, n)

    tau_arr = _broadcast_param(tau, (n,), "tau")
    if np.any(tau_arr < 0):
        raise ValueError("tau must be non-negative.")

    abs_error = np.abs(y_true_arr - y_pred_arr)
    hits = (abs_error <= tau_arr).astype(float)

    total_weight = float(w.sum())
    if total_weight <= 0:
        raise ValueError(
            "HR@τ is undefined: total sample_weight is zero. Check your weighting scheme."
        )

    return float(np.sum(w * hits) / total_weight)


def cwsl_sensitivity(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    R_list: Sequence[float] = (0.5, 1.0, 2.0, 3.0),
    co: float | ArrayLike = 1.0,
    sample_weight: ArrayLike | None = None,
) -> dict[float, float]:
    r"""
    Evaluate CWSL across a grid of cost ratios (cost sensitivity analysis).

    For each candidate ratio:

    $$
    R = \frac{c_u}{c_o}, \quad c_u = R \cdot c_o
    $$

    this helper computes:

    - ``cwsl(y_true, y_pred, cu=R*co, co=co, sample_weight=...)``

    Non-positive R values are ignored. If no positive values remain, raises ValueError.
    """
    results: dict[float, float] = {}

    for R in R_list:
        if R is None:
            continue
        Rf = float(R)
        if Rf <= 0:
            continue

        value = cwsl(
            y_true=y_true,
            y_pred=y_pred,
            cu=Rf * co,
            co=co,
            sample_weight=sample_weight,
        )
        results[Rf] = float(value)

    if not results:
        raise ValueError(
            "No valid R values in R_list (must contain at least one positive value)."
        )

    return results


def frs(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    cu: float | ArrayLike,
    co: float | ArrayLike,
    sample_weight: ArrayLike | None = None,
) -> float:
    r"""
    Compute Forecast Readiness Score (FRS).

    FRS is a simple composite score defined as:

    $$
    \mathrm{FRS} = \mathrm{NSL} - \mathrm{CWSL}
    $$

    where:
    - NSL measures the frequency of avoiding shortfall (higher is better)
    - CWSL measures asymmetric, demand-normalized cost (lower is better)
    """
    nsl_val = nsl(y_true=y_true, y_pred=y_pred, sample_weight=sample_weight)
    cwsl_val = cwsl(
        y_true=y_true,
        y_pred=y_pred,
        cu=cu,
        co=co,
        sample_weight=sample_weight,
    )
    return float(nsl_val - cwsl_val)
