"""
Internal utility helpers for `eb_metrics`.

This module contains internal helpers used across the Electric Barometer metrics
implementation. Functions in this module are **not** part of the public API and
may change without notice (module is prefixed with "_" and all function names
are prefixed with "_").

The utilities here primarily support:

- input normalization (array conversion and shape checks)
- scalar/array broadcasting for per-interval parameters
- sample weighting validation and normalization

Notes
-----
Downstream modules should prefer importing from `eb_metrics.metrics` or
`eb_metrics.frameworks`. This module is intended for internal reuse only.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def _to_1d_array(x: ArrayLike, name: str) -> np.ndarray:
    """
    Convert an input to a 1D NumPy float array with basic validation.

    Parameters
    ----------
    x : array-like
        Input values.
    name : str
        Name used in error messages.

    Returns
    -------
    numpy.ndarray
        1D array of dtype ``float``.

    Raises
    ------
    ValueError
        If ``x`` is not 1-dimensional or contains non-finite values.
    """
    arr = np.asarray(x, dtype=float)

    if arr.ndim != 1:
        raise ValueError(
            f"{name} must be a 1D array; got ndim={arr.ndim} and shape={arr.shape}"
        )

    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must contain only finite values (no NaN/inf).")

    return arr


def _broadcast_param(
    param: float | ArrayLike, shape: tuple[int, ...], name: str
) -> np.ndarray:
    """
    Broadcast a scalar or 1D parameter to a target 1D shape.

    This helper is used for parameters that can be specified either as:
    - a scalar (global value applied everywhere), or
    - a 1D array aligned to evaluation intervals.

    Parameters
    ----------
    param : float or array-like
        Parameter value(s) to broadcast.
    shape : tuple of int
        Target shape. Only 1D shapes are supported (e.g., ``(n_samples,)``).
    name : str
        Name used in error messages.

    Returns
    -------
    numpy.ndarray
        1D array of dtype ``float`` with the requested shape.

    Raises
    ------
    ValueError
        If ``shape`` is not 1D, if ``param`` cannot be broadcast to the target
        length, or if non-finite values are present.
    """
    if len(shape) != 1:
        raise ValueError(
            f"{name} broadcasting only supports 1D shapes; got shape={shape}"
        )

    length = int(shape[0])
    arr = np.asarray(param, dtype=float)

    if arr.ndim == 0:
        out = np.full(length, float(arr))
    elif arr.ndim == 1 and arr.shape[0] == length:
        out = arr
    else:
        raise ValueError(
            f"{name} must be a scalar or 1D array of length {length}; got shape {arr.shape}"
        )

    if not np.all(np.isfinite(out)):
        raise ValueError(f"{name} must contain only finite values (no NaN/inf).")

    return out


def _handle_sample_weight(
    sample_weight: ArrayLike | None,
    length: int,
    *,
    dtype: type = float,
) -> np.ndarray:
    """
    Normalize ``sample_weight`` to a 1D non-negative NumPy array.

    Parameters
    ----------
    sample_weight : array-like, optional
        Optional weights. May be:
        - ``None`` (interpreted as all ones),
        - a scalar (broadcast to length), or
        - a 1D array of length ``length``.
    length : int
        Required length of the resulting weight vector.
    dtype : type, default=float
        Output dtype (commonly ``float``).

    Returns
    -------
    numpy.ndarray
        1D array of shape ``(length,)`` with non-negative, finite weights.

    Raises
    ------
    ValueError
        If weights are negative, non-finite, or cannot be broadcast to length.
    """
    if length < 0:
        raise ValueError(f"length must be non-negative; got {length}")

    if sample_weight is None:
        w = np.ones(length, dtype=dtype)
        return w

    w = np.asarray(sample_weight, dtype=dtype)

    if w.ndim == 0:
        w = np.full(length, float(w), dtype=dtype)
    elif w.ndim == 1 and w.shape[0] == length:
        # already aligned
        pass
    else:
        raise ValueError(
            f"sample_weight must be a scalar or 1D array of length {length}; got shape {w.shape}"
        )

    if not np.all(np.isfinite(w)):
        raise ValueError("sample_weight must contain only finite values (no NaN/inf).")
    if np.any(w < 0):
        raise ValueError("sample_weight must be non-negative.")

    return w
