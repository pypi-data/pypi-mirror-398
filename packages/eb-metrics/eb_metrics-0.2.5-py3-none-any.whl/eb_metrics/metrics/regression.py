"""
Classical regression and forecasting error metrics.

This module provides standard symmetric error metrics commonly used for baseline
comparison and diagnostic validation. These metrics complement Electric
Barometer's asymmetric and service-oriented measures by providing familiar
reference points (e.g., MAE, RMSE, MAPE).

Conceptual Electric Barometer metrics (e.g., CWSL, NSL) are implemented in other
modules. The functions here are intentionally lightweight and dependency-minimal.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

__all__ = [
    "mae",
    "mape",
    "mase",
    "medae",
    "mse",
    "msle",
    "rmse",
    "rmsle",
    "smape",
    "wmape",
]


# ----------------------------------------------------------------------
# Internal utilities
# ----------------------------------------------------------------------
def _validate_shapes(
    y_true: ArrayLike, y_pred: ArrayLike
) -> tuple[np.ndarray, np.ndarray]:
    """Convert inputs to float arrays and require identical shapes."""
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    if y_true_arr.shape != y_pred_arr.shape:
        raise ValueError(
            "y_true and y_pred must have identical shapes; "
            f"got {y_true_arr.shape} and {y_pred_arr.shape}"
        )
    return y_true_arr, y_pred_arr


# ----------------------------------------------------------------------
# Basic regression metrics
# ----------------------------------------------------------------------
def mae(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Mean Absolute Error (MAE).

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth values.
    y_pred : array-like of shape (n_samples,)
        Predicted values.

    Returns
    -------
    float
        Mean absolute error. Lower is better.
    """
    y_true_arr, y_pred_arr = _validate_shapes(y_true, y_pred)
    return float(np.mean(np.abs(y_true_arr - y_pred_arr)))


def mse(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Mean Squared Error (MSE).

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth values.
    y_pred : array-like of shape (n_samples,)
        Predicted values.

    Returns
    -------
    float
        Mean squared error. Lower is better.
    """
    y_true_arr, y_pred_arr = _validate_shapes(y_true, y_pred)
    return float(np.mean((y_true_arr - y_pred_arr) ** 2))


def rmse(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Root Mean Squared Error (RMSE).

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth values.
    y_pred : array-like of shape (n_samples,)
        Predicted values.

    Returns
    -------
    float
        Root mean squared error. Lower is better.
    """
    return float(np.sqrt(mse(y_true, y_pred)))


def mape(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    r"""Mean Absolute Percentage Error (MAPE).

    MAPE is computed over samples where ``y_true != 0``:

    $$
    \mathrm{MAPE} = 100 \cdot \mathrm{mean}\left(\left|\frac{y-\hat{y}}{y}\right|\right)
    $$

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth values.
    y_pred : array-like of shape (n_samples,)
        Predicted values.

    Returns
    -------
    float
        Mean absolute percentage error in percent. Lower is better.

    Raises
    ------
    ValueError
        If all values of ``y_true`` are zero (MAPE undefined).

    Notes
    -----
    MAPE can be unstable when ``y_true`` is near zero. Consider WMAPE or a
    domain-specific metric (e.g., CWSL) when percentage behavior is undesirable.
    """
    y_true_arr, y_pred_arr = _validate_shapes(y_true, y_pred)
    mask = y_true_arr != 0
    if not np.any(mask):
        raise ValueError("MAPE undefined when all y_true values are zero.")
    pct = np.abs((y_true_arr[mask] - y_pred_arr[mask]) / y_true_arr[mask])
    return float(np.mean(pct) * 100.0)


def wmape(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    r"""Weighted Mean Absolute Percentage Error (WMAPE).

    WMAPE is also commonly described as demand-normalized absolute error:

    $$
    \mathrm{WMAPE} = 100 \cdot \frac{\sum_i |y_i-\hat{y}_i|}{\sum_i |y_i|}
    $$

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth values.
    y_pred : array-like of shape (n_samples,)
        Predicted values.

    Returns
    -------
    float
        WMAPE in percent. Lower is better.

    Raises
    ------
    ValueError
        If ``sum(|y_true|) == 0`` (WMAPE undefined).

    Notes
    -----
    WMAPE is symmetric: it does not distinguish underprediction from
    overprediction. Use CWSL when directional cost asymmetry matters.
    """
    y_true_arr, y_pred_arr = _validate_shapes(y_true, y_pred)
    numerator = np.sum(np.abs(y_true_arr - y_pred_arr))
    denominator = np.sum(np.abs(y_true_arr))
    if denominator == 0:
        raise ValueError("WMAPE undefined when sum(|y_true|) == 0.")
    return float(numerator / denominator * 100.0)


def medae(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Median Absolute Error (MedAE).

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth values.
    y_pred : array-like of shape (n_samples,)
        Predicted values.

    Returns
    -------
    float
        Median absolute error. Lower is better.
    """
    y_true_arr, y_pred_arr = _validate_shapes(y_true, y_pred)
    return float(np.median(np.abs(y_true_arr - y_pred_arr)))


def smape(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    r"""Symmetric Mean Absolute Percentage Error (sMAPE).

    This implementation follows a common competition definition:

    $$
    \mathrm{sMAPE} = 200 \cdot \mathrm{mean}\left(\frac{|y-\hat{y}|}{|y| + |\hat{y}|}\right)
    $$

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth values.
    y_pred : array-like of shape (n_samples,)
        Predicted values.

    Returns
    -------
    float
        sMAPE in percent. Lower is better.

    Notes
    -----
    If ``|y| + |y_pred| == 0`` for all samples, this function returns ``0.0``.
    """
    y_true_arr, y_pred_arr = _validate_shapes(y_true, y_pred)
    denom = np.abs(y_true_arr) + np.abs(y_pred_arr)
    mask = denom != 0
    if not np.any(mask):
        return 0.0
    ratio = np.abs(y_true_arr[mask] - y_pred_arr[mask]) / denom[mask]
    return float(np.mean(ratio) * 200.0)


# ----------------------------------------------------------------------
# Log-based metrics
# ----------------------------------------------------------------------
def msle(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    r"""Mean Squared Log Error (MSLE).

    MSLE is defined as:

    $$
    \mathrm{MSLE} = \mathrm{mean}\left((\log(1+y) - \log(1+\hat{y}))^2\right)
    $$

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth values. Must be non-negative.
    y_pred : array-like of shape (n_samples,)
        Predicted values. Must be non-negative.

    Returns
    -------
    float
        Mean squared log error. Lower is better.

    Raises
    ------
    ValueError
        If any value in ``y_true`` or ``y_pred`` is negative.

    Notes
    -----
    MSLE down-weights large absolute errors at high magnitudes and is commonly
    used when relative error is more meaningful than absolute error.
    """
    y_true_arr, y_pred_arr = _validate_shapes(y_true, y_pred)

    if np.any(y_true_arr < 0) or np.any(y_pred_arr < 0):
        raise ValueError("MSLE requires non-negative y_true and y_pred.")

    log_t = np.log1p(y_true_arr)
    log_p = np.log1p(y_pred_arr)
    return float(np.mean((log_t - log_p) ** 2))


def rmsle(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Root Mean Squared Log Error (RMSLE).

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth values. Must be non-negative.
    y_pred : array-like of shape (n_samples,)
        Predicted values. Must be non-negative.

    Returns
    -------
    float
        Root mean squared log error. Lower is better.
    """
    return float(np.sqrt(msle(y_true, y_pred)))


# ----------------------------------------------------------------------
# Scaled metrics
# ----------------------------------------------------------------------
def mase(y_true: ArrayLike, y_pred: ArrayLike, y_naive: ArrayLike) -> float:
    r"""Mean Absolute Scaled Error (MASE).

    MASE scales the model MAE by the MAE of a naive forecast:

    $$
    \mathrm{MASE} = \frac{\mathrm{MAE}(y,\hat{y})}{\mathrm{MAE}(y, y^{\text{naive}})}
    $$

    where ``y_naive`` is typically a naive baseline such as $y_{t-1}$.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth values.
    y_pred : array-like of shape (n_samples,)
        Predicted values.
    y_naive : array-like of shape (n_samples,)
        Naive forecast values aligned to ``y_true``.

    Returns
    -------
    float
        MASE value. Lower is better.

    Raises
    ------
    ValueError
        If the naive MAE is zero (MASE undefined).

    Notes
    -----
    MASE is scale-free and can be compared across series with different
    magnitudes, assuming the naive baseline is meaningful.
    """
    y_true_arr, y_pred_arr = _validate_shapes(y_true, y_pred)
    y_true_arr2, y_naive_arr = _validate_shapes(y_true, y_naive)

    mae_model = np.mean(np.abs(y_true_arr - y_pred_arr))
    mae_naive = np.mean(np.abs(y_true_arr2 - y_naive_arr))

    if mae_naive == 0:
        raise ValueError("MASE undefined because naive MAE is zero.")

    return float(mae_model / mae_naive)
