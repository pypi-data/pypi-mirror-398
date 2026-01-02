"""
Asymmetric loss metrics for the Electric Barometer ecosystem.

This module contains loss-like metrics that explicitly encode operational
asymmetry between *underbuild* (shortfall; forecasting below realized demand)
and *overbuild* (excess; forecasting above realized demand).

The primary metric implemented here is **Cost-Weighted Service Loss (CWSL)**,
a demand-normalized loss that generalizes weighted MAPE by assigning distinct
per-unit costs to shortfall and overbuild.

Conceptual definitions, motivation, and interpretation are documented in the
companion research repository (`eb-papers`).
"""

__all__ = ["cwsl"]


import numpy as np
from numpy.typing import ArrayLike

from .._utils import (
    _broadcast_param,
    _handle_sample_weight,
    _to_1d_array,
)


def cwsl(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    cu: float | ArrayLike,
    co: float | ArrayLike,
    sample_weight: ArrayLike | None = None,
) -> float:
    r"""
    Compute Cost-Weighted Service Loss (CWSL).

    CWSL is a demand-normalized, directionally-aware loss that penalizes
    **shortfalls** and **overbuilds** using explicit per-unit costs.

    For each interval $i$:

    $$
    \begin{aligned}
    s_i &= \max(0, y_i - \hat{y}_i) \\
    o_i &= \max(0, \hat{y}_i - y_i) \\
    \text{cost}_i &= c_{u,i} \; s_i + c_{o,i} \; o_i
    \end{aligned}
    $$

    and the aggregated metric is:

    $$
    \mathrm{CWSL} = \frac{\sum_i w_i \; \text{cost}_i}{\sum_i w_i \; y_i}
    $$

    where $w_i$ are optional sample weights (default $w_i = 1$).
    Lower values indicate better performance.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Realized demand $y$. Must be non-negative.

    y_pred : array-like of shape (n_samples,)
        Forecast demand $\hat{y}$. Must be non-negative and have the same
        shape as ``y_true``.

    cu : float or array-like of shape (n_samples,)
        Per-unit shortfall cost $c_u$. Can be a scalar (global cost) or a
        1D array specifying per-interval costs. Must be non-negative.

    co : float or array-like of shape (n_samples,)
        Per-unit overbuild cost $c_o$. Can be a scalar (global cost) or a
        1D array specifying per-interval costs. Must be non-negative.

    sample_weight : float or array-like of shape (n_samples,), optional
        Optional non-negative weights per interval. If ``None``, all intervals
        receive weight ``1.0``.

    Returns
    -------
    float
        The CWSL value. Lower is better.

    Raises
    ------
    ValueError
        If ``y_true`` and ``y_pred`` have different shapes, if any demand or
        forecast values are negative, if any costs are negative, or if the
        metric is undefined due to zero total (weighted) demand with positive
        total (weighted) cost.

    Notes
    -----
    - When ``cu == co`` (up to a constant scaling), CWSL behaves similarly to a
      demand-normalized absolute error (wMAPE-like), but retains explicit cost
      semantics.
    - If total (weighted) demand is zero and total (weighted) cost is zero,
      this implementation returns ``0.0``.
    - If total (weighted) demand is zero but total (weighted) cost is positive,
      the metric is undefined under this formulation and a ``ValueError`` is
      raised.

    References
    ----------
    Electric Barometer Technical Note: Cost-Weighted Service Loss (CWSL).
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

    # Broadcast cu and co (allow scalar or 1D array of length n)
    cu_arr = _broadcast_param(cu, (n,), "cu")
    co_arr = _broadcast_param(co, (n,), "co")

    if np.any(cu_arr < 0):
        raise ValueError("cu must be non-negative.")
    if np.any(co_arr < 0):
        raise ValueError("co must be non-negative.")

    # Sample weights
    w = _handle_sample_weight(sample_weight, n, dtype=float)

    # Shortfall and overbuild components
    shortfall = np.maximum(0.0, y_true_arr - y_pred_arr)
    overbuild = np.maximum(0.0, y_pred_arr - y_true_arr)

    # Weighted cost and weighted demand
    cost = cu_arr * shortfall + co_arr * overbuild
    weighted_cost = cost * w
    weighted_demand = y_true_arr * w

    total_cost = float(weighted_cost.sum())
    total_demand = float(weighted_demand.sum())

    if total_demand > 0:
        return total_cost / total_demand

    # total_demand == 0
    if total_cost == 0:
        # No demand and no cost → define CWSL as 0.0
        return 0.0

    # Cost but no demand → undefined metric under this formulation
    raise ValueError(
        "CWSL is undefined: total (weighted) demand is zero while total (weighted) "
        "cost is positive. Check your data slice or weighting scheme."
    )
