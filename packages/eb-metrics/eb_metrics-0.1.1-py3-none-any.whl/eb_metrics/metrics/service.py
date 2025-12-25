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
"""

from typing import Dict, Sequence, Union

import numpy as np
from numpy.typing import ArrayLike

from .._utils import (
    _to_1d_array,
    _broadcast_param,
    _handle_sample_weight,
)
from .loss import cwsl

__all__ = ["nsl", "ud", "hr_at_tau", "frs", "cwsl_sensitivity"]


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

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Realized demand. Must be non-negative.

    y_pred : array-like of shape (n_samples,)
        Forecast demand. Must be non-negative and have the same shape as
        ``y_true``.

    sample_weight : float or array-like of shape (n_samples,), optional
        Optional non-negative weights per interval. If provided, NSL is computed
        as a weighted fraction. If total weight is zero, NSL is undefined and a
        ``ValueError`` is raised.

    Returns
    -------
    float
        NSL value in [0, 1]. Higher indicates better shortfall avoidance.

    Raises
    ------
    ValueError
        If inputs are invalid (shape mismatch, negative values), or if total
        sample weight is zero.

    Notes
    -----
    - NSL is a *service reliability* measure: it does not quantify how large a
      shortfall is—only whether a shortfall occurred.
    - UD complements NSL by measuring shortfall magnitude when shortfalls occur.

    References
    ----------
    Electric Barometer Technical Note: No Shortfall Level (NSL).
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

    # Hit = no shortfall → y_pred >= y_true
    hits = (y_pred_arr >= y_true_arr).astype(float)

    weighted_hits = w * hits
    total_weight = float(w.sum())

    if total_weight <= 0:
        raise ValueError(
            "NSL is undefined: total sample_weight is zero. "
            "Check your weighting scheme."
        )

    return float(weighted_hits.sum() / total_weight)


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

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Realized demand. Must be non-negative.

    y_pred : array-like of shape (n_samples,)
        Forecast demand. Must be non-negative and have the same shape as
        ``y_true``.

    sample_weight : float or array-like of shape (n_samples,), optional
        Optional non-negative weights per interval. If provided, UD is computed
        as a weighted average. If total weight is zero, UD is undefined and a
        ``ValueError`` is raised.

    Returns
    -------
    float
        UD value (units match ``y_true``/``y_pred``). Lower indicates better
        shortfall control.

    Raises
    ------
    ValueError
        If inputs are invalid (shape mismatch, negative values), or if total
        sample weight is zero.

    Notes
    -----
    - UD ignores overbuild entirely; it is a pure *shortfall severity* measure.
    - UD is often interpreted alongside NSL:
      high NSL + low UD indicates strong service consistency.

    References
    ----------
    Electric Barometer Technical Note: Underbuild Depth (UD).
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

    weighted_shortfall = w * shortfall
    total_weight = float(w.sum())

    if total_weight <= 0:
        raise ValueError(
            "UD is undefined: total sample_weight is zero. "
            "Check your weighting scheme."
        )

    return float(weighted_shortfall.sum() / total_weight)


def hr_at_tau(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    tau: Union[float, ArrayLike],
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

    Higher values are better, with $\mathrm{HR@\tau} \in [0, 1]$.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Realized demand. Must be non-negative.

    y_pred : array-like of shape (n_samples,)
        Forecast demand. Must be non-negative and have the same shape as
        ``y_true``.

    tau : float or array-like of shape (n_samples,)
        Non-negative absolute error tolerance. Can be:
        - scalar: same tolerance for all intervals
        - 1D array: per-interval tolerance

    sample_weight : float or array-like of shape (n_samples,), optional
        Optional non-negative weights per interval. If provided, HR@τ is computed
        as a weighted fraction. If total weight is zero, HR@τ is undefined and a
        ``ValueError`` is raised.

    Returns
    -------
    float
        HR@τ value in [0, 1]. Higher indicates more intervals within tolerance.

    Raises
    ------
    ValueError
        If inputs are invalid (shape mismatch, negative values), if ``tau`` is
        negative anywhere, or if total sample weight is zero.

    Notes
    -----
    - HR@τ is a symmetric tolerance measure; it treats underbuild and overbuild
      equally within the tolerance band.
    - Use HR@τ alongside asymmetric metrics (e.g., CWSL) when operational costs
      differ by direction.

    References
    ----------
    Electric Barometer Technical Note: HR@τ (Hit Rate within Tolerance).
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

    weighted_hits = w * hits
    total_weight = float(w.sum())

    if total_weight <= 0:
        raise ValueError(
            "HR@τ is undefined: total sample_weight is zero. "
            "Check your weighting scheme."
        )

    return float(weighted_hits.sum() / total_weight)


def cwsl_sensitivity(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    R_list: Sequence[float] = (0.5, 1.0, 2.0, 3.0),
    co: Union[float, ArrayLike] = 1.0,
    sample_weight: ArrayLike | None = None,
) -> Dict[float, float]:
    r"""
    Evaluate CWSL across a grid of cost ratios (cost sensitivity analysis).

    This helper computes Cost-Weighted Service Loss (CWSL) for each candidate
    cost ratio:

    $$
    R = c_u / c_o
    $$

    holding ``co`` fixed and setting:

    $$
    c_u = R \cdot c_o
    $$

    for each value in ``R_list``.

    This provides a simple way to assess how model ranking or absolute loss
    changes under alternative assumptions about shortfall vs. overbuild cost.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Realized demand. Must be non-negative.

    y_pred : array-like of shape (n_samples,)
        Forecast demand. Must be non-negative and have the same shape as
        ``y_true``.

    R_list : sequence of float, default=(0.5, 1.0, 2.0, 3.0)
        Candidate cost ratios to evaluate. Only strictly positive values are
        used.

    co : float or array-like of shape (n_samples,), default=1.0
        Overbuild cost $c_o$. Can be scalar or per-interval.

    sample_weight : float or array-like of shape (n_samples,), optional
        Optional non-negative weights per interval, passed through to CWSL.

    Returns
    -------
    dict[float, float]
        Mapping ``{R: cwsl_value}`` for each valid ``R`` in ``R_list``.

    Raises
    ------
    ValueError
        If ``R_list`` contains no positive values, or if inputs are invalid or
        CWSL is undefined for the given data slice.

    Notes
    -----
    - This is a *pure evaluation* utility; it does not attempt to infer the
      “correct” cost ratio. For that, see cost-ratio estimation utilities.

    References
    ----------
    Electric Barometer Technical Note: Cost Sensitivity Utilities for CWSL.
    """
    results: Dict[float, float] = {}

    for R in R_list:
        if R <= 0:
            continue

        # cu = R * co
        value = cwsl(
            y_true=y_true,
            y_pred=y_pred,
            cu=float(R) * co,
            co=co,
            sample_weight=sample_weight,
        )
        results[float(R)] = float(value)

    if not results:
        raise ValueError(
            "No valid R values in R_list (must contain at least one positive value)."
        )

    return results


def frs(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    cu: Union[float, ArrayLike],
    co: Union[float, ArrayLike],
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

    This construction rewards forecasts that simultaneously:
    - maintain high service reliability (high NSL), and
    - avoid costly asymmetric error (low CWSL).

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Realized demand. Must be non-negative.

    y_pred : array-like of shape (n_samples,)
        Forecast demand. Must be non-negative and have the same shape as
        ``y_true``.

    cu : float or array-like of shape (n_samples,)
        Per-unit shortfall cost passed through to CWSL.

    co : float or array-like of shape (n_samples,)
        Per-unit overbuild cost passed through to CWSL.

    sample_weight : float or array-like of shape (n_samples,), optional
        Optional non-negative weights per interval, applied consistently to NSL
        and CWSL.

    Returns
    -------
    float
        Forecast Readiness Score. Higher indicates better readiness. Values are
        typically bounded above by 1, but can be negative depending on cost and
        forecast error.

    Raises
    ------
    ValueError
        If inputs are invalid or CWSL is undefined for the given data slice.

    Notes
    -----
    This metric is intentionally simple and should be interpreted as a
    readiness-oriented summary rather than a standalone loss function.

    References
    ----------
    Electric Barometer Technical Note: Forecast Readiness Score (FRS).
    """
    # We rely on the existing validation in nsl() and cwsl()
    nsl_val = nsl(y_true=y_true, y_pred=y_pred, sample_weight=sample_weight)
    cwsl_val = cwsl(
        y_true=y_true,
        y_pred=y_pred,
        cu=cu,
        co=co,
        sample_weight=sample_weight,
    )
    return float(nsl_val - cwsl_val)
