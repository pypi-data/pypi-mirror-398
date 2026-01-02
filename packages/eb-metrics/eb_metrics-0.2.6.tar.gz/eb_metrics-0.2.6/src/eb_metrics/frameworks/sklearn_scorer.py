"""
scikit-learn integration for Electric Barometer metrics.

This module provides scikit-learn-compatible scoring utilities built on top of
Electric Barometer metrics. The primary entry point is :func:`cwsl_scorer`,
which produces a scorer suitable for use with ``GridSearchCV``,
``RandomizedSearchCV``, ``cross_val_score``, and related tooling.

Notes
-----
- Electric Barometer's Cost-Weighted Service Loss (CWSL) is a *loss*
  (lower is better). scikit-learn model selection APIs expect a *score*
  (higher is better). The scorer produced here returns **negative CWSL**
  so it can be maximized.
- Conceptual definitions of CWSL and its cost parameters are documented in
  the companion research repository (`eb-papers`).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import ArrayLike

from eb_metrics.metrics import cwsl

__all__ = ["cwsl_loss", "cwsl_scorer"]


def cwsl_loss(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    *,
    cu: float,
    co: float,
    sample_weight: ArrayLike | None = None,
) -> float:
    r"""
    Compute the (positive) Cost-Weighted Service Loss (CWSL) for scikit-learn usage.

    This helper is a thin wrapper around :func:`eb_metrics.metrics.cwsl` that:

    - enforces strict positivity of ``cu`` and ``co`` (to align with typical
      scikit-learn scorer usage), and
    - converts inputs to ``numpy.ndarray`` prior to evaluation.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Realized demand values.
    y_pred : array-like of shape (n_samples,)
        Forecast values.
    cu : float
        Per-unit cost of underbuild (shortfall). Must be strictly positive.
    co : float
        Per-unit cost of overbuild (excess). Must be strictly positive.
    sample_weight : array-like of shape (n_samples,), optional
        Optional per-sample weights passed through to CWSL.

    Returns
    -------
    float
        Positive CWSL value (lower is better).

    Raises
    ------
    ValueError
        If ``cu`` or ``co`` are not strictly positive, or if the underlying CWSL
        computation is undefined for the given inputs.

    Notes
    -----
    CWSL is defined as a demand-normalized asymmetric cost:

    $$
    \mathrm{CWSL} = \frac{\sum_i w_i \left(c_u s_i + c_o o_i\right)}{\sum_i w_i y_i},
    \quad
    s_i = \max(0, y_i-\hat{y}_i),
    \quad
    o_i = \max(0, \hat{y}_i-y_i)
    $$

    References
    ----------
    Electric Barometer Technical Note: Cost-Weighted Service Loss (CWSL).
    """
    if cu <= 0.0:
        raise ValueError("cu must be strictly positive.")
    if co <= 0.0:
        raise ValueError("co must be strictly positive.")

    return cwsl(
        y_true=np.asarray(y_true, dtype=float),
        y_pred=np.asarray(y_pred, dtype=float),
        cu=cu,
        co=co,
        sample_weight=sample_weight,
    )


def cwsl_scorer(cu: float, co: float) -> Callable:
    r"""
    Build a scikit-learn scorer based on Cost-Weighted Service Loss (CWSL).

    The returned object can be used wherever scikit-learn expects a scorer, for
    example:

    - ``GridSearchCV(..., scoring=cwsl_scorer(cu=2.0, co=1.0))``
    - ``cross_val_score(..., scoring=cwsl_scorer(cu=2.0, co=1.0))``

    Parameters
    ----------
    cu : float
        Per-unit cost of underbuild (shortfall). Must be strictly positive.
    co : float
        Per-unit cost of overbuild (excess). Must be strictly positive.

    Returns
    -------
    Callable
        A scikit-learn scorer that returns **negative CWSL** (higher is better).

    Notes
    -----
    scikit-learn assumes scores are maximized. Because CWSL is a loss (lower is
    better), this scorer is configured with ``greater_is_better=False`` so
    scikit-learn negates the value internally.

    In other words, the score returned by scikit-learn is:

    $$
    \text{score} = -\,\mathrm{CWSL}
    $$

    References
    ----------
    Electric Barometer Technical Note: Cost-Weighted Service Loss (CWSL).
    """
    if cu <= 0.0:
        raise ValueError("cu must be strictly positive.")
    if co <= 0.0:
        raise ValueError("co must be strictly positive.")

    from sklearn.metrics import make_scorer

    def _loss(
        y_true: ArrayLike,
        y_pred: ArrayLike,
        sample_weight: ArrayLike | None = None,
        **kwargs,
    ) -> float:
        # Accept **kwargs to remain compatible with sklearn passing metadata keys.
        # (e.g., needs_proba / needs_threshold in some scorer pathways)
        return cwsl_loss(
            y_true=y_true,
            y_pred=y_pred,
            cu=cu,
            co=co,
            sample_weight=sample_weight,
        )

    # greater_is_better=False -> sklearn negates the loss internally,
    # so the scorer returns -CWSL and can be maximized.
    return make_scorer(
        _loss,
        greater_is_better=False,
        response_method="predict",
    )
