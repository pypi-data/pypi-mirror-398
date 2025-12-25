from __future__ import annotations

"""
Cost-ratio utilities for the Electric Barometer ecosystem.

This module contains helpers for selecting and analyzing the **asymmetric cost
ratio** used throughout Electric Barometer metrics.

In Electric Barometer notation, the cost ratio is:

    R = c_u / c_o

where:
- c_u is the per-unit cost of *underbuild* (shortfall; forecasting below realized demand)
- c_o is the per-unit cost of *overbuild* (excess; forecasting above realized demand)

These utilities do not define the metrics themselves; they support choosing
reasonable cost-ratio values for evaluation and sensitivity analysis. Conceptual
definitions and motivation are provided in the companion research repository
(`eb-papers`).
"""

from typing import Sequence, Union

import numpy as np
from numpy.typing import ArrayLike

from .._utils import _broadcast_param, _handle_sample_weight, _to_1d_array


def estimate_R_cost_balance(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    R_grid: Sequence[float] = (0.5, 1.0, 2.0, 3.0),
    co: Union[float, ArrayLike] = 1.0,
    sample_weight: ArrayLike | None = None,
) -> float:
    r"""
    Estimate a global cost ratio $R = c_u / c_o$ via cost balance.

    This routine selects a single, global cost ratio $R$ by searching a
    candidate grid and choosing the value where the **total weighted underbuild
    cost** is closest to the **total weighted overbuild cost**.

    For each candidate $R$ in ``R_grid``:

    $$
    \begin{aligned}
    c_{u,i} &= R \cdot c_{o,i} \\
    s_i &= \max(0, y_i - \hat{y}_i) \\
    e_i &= \max(0, \hat{y}_i - y_i) \\
    C_u(R) &= \sum_i w_i \; c_{u,i} \; s_i \\
    C_o(R) &= \sum_i w_i \; c_{o,i} \; e_i
    \end{aligned}
    $$

    and the selected value is:

    $$
    R^* = \arg\min_R \; \left| C_u(R) - C_o(R) \right|.
    $$

    The returned $R^*$ can be used as:
    - a reasonable default global cost ratio for evaluation, and/or
    - the center of a sensitivity sweep (e.g., ``{R*/2, R*, 2*R*}``).

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Realized demand (non-negative).

    y_pred : array-like of shape (n_samples,)
        Forecast demand (non-negative). Must have the same shape as ``y_true``.

    R_grid : sequence of float, default=(0.5, 1.0, 2.0, 3.0)
        Candidate cost ratios $R$ to search over. Only **strictly positive**
        values are considered.

    co : float or array-like of shape (n_samples,), default=1.0
        Overbuild cost $c_o$ per unit. Can be:

        - scalar: same overbuild cost for all intervals
        - 1D array: per-interval overbuild cost

        For each $R$, the implied underbuild cost is
        $c_{u,i} = R \cdot c_{o,i}$.

    sample_weight : float or array-like of shape (n_samples,), optional
        Optional non-negative weights per interval used to weight the cost
        aggregation. If ``None``, all intervals receive weight ``1.0``.

    Returns
    -------
    float
        The value in ``R_grid`` that minimizes
        $\left| C_u(R) - C_o(R) \right|$.

        If multiple values yield the same minimal gap, the first such value in
        the (filtered) grid is returned, except in the degenerate *perfect
        forecast* case (zero error everywhere), where the candidate closest to
        ``1.0`` is returned.

    Raises
    ------
    ValueError
        If inputs are invalid (e.g., negative ``y_true`` or ``y_pred``), if
        ``R_grid`` is empty, or if it contains no positive values.

    Notes
    -----
    This helper is intentionally simple: it does **not** infer cost structure
    from business inputs, nor does it estimate per-item costs. It provides a
    reproducible, data-driven way to select a reasonable global $R$ given
    realized outcomes and forecast behavior.

    References
    ----------
    Electric Barometer Technical Note: Cost Ratio Estimation (Choosing $R$).
    """
    y_true_arr = _to_1d_array(y_true, "y_true")
    y_pred_arr = _to_1d_array(y_pred, "y_pred")

    if y_true_arr.shape != y_pred_arr.shape:
        raise ValueError(
            "y_true and y_pred must have the same shape; "
            f"got {y_true_arr.shape} and {y_pred_arr.shape}"
        )

    if np.any(y_true_arr < 0) or np.any(y_pred_arr < 0):
        raise ValueError("y_true and y_pred must be non-negative.")

    co_arr = _broadcast_param(co, y_true_arr.shape, "co")
    if np.any(co_arr <= 0):
        raise ValueError("co must be strictly positive.")

    w = _handle_sample_weight(sample_weight, y_true_arr.shape[0], dtype=float)

    shortfall = np.maximum(0.0, y_true_arr - y_pred_arr)
    overbuild = np.maximum(0.0, y_pred_arr - y_true_arr)

    R_grid_arr = np.asarray(R_grid, dtype=float)

    if R_grid_arr.ndim != 1 or R_grid_arr.size == 0:
        raise ValueError("R_grid must be a non-empty 1D sequence of floats.")

    # Keep only strictly positive R values
    positive_R = R_grid_arr[R_grid_arr > 0]
    if positive_R.size == 0:
        raise ValueError("R_grid must contain at least one positive value.")

    # Degenerate case: perfect forecast (no error anywhere)
    if np.all(shortfall == 0.0) and np.all(overbuild == 0.0):
        # Choose the R closest to 1.0
        idx = int(np.argmin(np.abs(positive_R - 1.0)))
        return float(positive_R[idx])

    best_R: float | None = None
    best_gap: float | None = None

    for R in positive_R:
        cu_arr = R * co_arr

        under_cost = float(np.sum(w * cu_arr * shortfall))
        over_cost = float(np.sum(w * co_arr * overbuild))

        gap = abs(under_cost - over_cost)

        if best_gap is None or gap < best_gap:
            best_gap = gap
            best_R = float(R)

    # best_R must be set because positive_R is non-empty
    return float(best_R)
