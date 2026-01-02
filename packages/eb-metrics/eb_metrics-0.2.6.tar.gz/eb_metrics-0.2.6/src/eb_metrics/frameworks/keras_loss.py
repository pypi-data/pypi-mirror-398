"""
Keras / TensorFlow integration for Electric Barometer metrics.

This module provides TensorFlow-native utilities that allow Electric Barometer
loss definitions (specifically CWSL) to be used as training objectives in
Keras models.

Notes
-----
- TensorFlow is an optional dependency. This module imports TensorFlow lazily.
- Electric Barometer's Cost-Weighted Service Loss (CWSL) is defined as a
  demand-normalized, asymmetric cost function. Here it is implemented as a
  per-sample loss suitable for gradient-based training.
- Conceptual definitions and interpretation are documented in the companion
  research repository (`eb-papers`).
"""

from __future__ import annotations

from collections.abc import Callable

__all__ = ["make_cwsl_keras_loss"]


def make_cwsl_keras_loss(cu: float, co: float) -> Callable:
    r"""
    Create a Keras-compatible loss implementing Cost-Weighted Service Loss (CWSL).

    This factory returns a TensorFlow/Keras loss function that mirrors the
    NumPy-based CWSL metric but is shaped to work in deep learning workflows.

    The returned loss function has signature:

    ``loss(y_true, y_pred) -> tf.Tensor``

    and returns a tensor of shape ``(batch_size,)`` (one loss value per example),
    which Keras will then reduce according to the configured reduction mode.

    For each sample, CWSL is computed as:

    $$
    \begin{aligned}
    s &= \max(0, y - \hat{y}) \\
    o &= \max(0, \hat{y} - y) \\
    \mathrm{CWSL} &= \frac{c_u \sum s + c_o \sum o}{\sum y}
    \end{aligned}
    $$

    where the summations reduce over the final axis (e.g., forecast horizon).

    Parameters
    ----------
    cu : float
        Per-unit cost of underbuild (shortfall). Must be strictly positive.
    co : float
        Per-unit cost of overbuild (excess). Must be strictly positive.

    Returns
    -------
    Callable
        A Keras-compatible loss function ``loss(y_true, y_pred)`` returning a
        per-sample CWSL tensor of shape ``(batch_size,)``.

    Raises
    ------
    ImportError
        If TensorFlow is not installed.
    ValueError
        If ``cu`` or ``co`` are not strictly positive.

    Notes
    -----
    - Inputs are cast to ``tf.float32``.
    - The reduction is performed over the **last axis**. This supports both:
      - ``(batch_size, horizon)`` tensors (typical forecasting setup), and
      - ``(batch_size,)`` tensors (single-step forecasting), where reduction over
        the last axis still behaves correctly.
    - Division by zero is avoided by clamping the per-sample demand denominator
      with Keras epsilon.

    References
    ----------
    Electric Barometer Technical Note: Cost-Weighted Service Loss (CWSL).
    """
    if cu <= 0.0:
        raise ValueError("cu must be strictly positive.")
    if co <= 0.0:
        raise ValueError("co must be strictly positive.")

    try:
        import tensorflow as tf  # type: ignore[import]
    except ImportError as e:  # pragma: no cover - optional dependency path
        raise ImportError(
            "TensorFlow is required to use make_cwsl_keras_loss. "
            "Install it via `pip install tensorflow`."
        ) from e

    cu_t = tf.constant(cu, dtype=tf.float32)
    co_t = tf.constant(co, dtype=tf.float32)

    def cwsl_loss(y_true, y_pred):
        """
        Per-sample CWSL loss.

        Parameters
        ----------
        y_true : tf.Tensor
            Realized demand values.
        y_pred : tf.Tensor
            Forecast values.

        Returns
        -------
        tf.Tensor
            Per-sample CWSL of shape ``(batch_size,)``.
        """
        y_true_f = tf.cast(y_true, tf.float32)
        y_pred_f = tf.cast(y_pred, tf.float32)

        shortfall = tf.nn.relu(y_true_f - y_pred_f)
        overbuild = tf.nn.relu(y_pred_f - y_true_f)

        cost = cu_t * shortfall + co_t * overbuild

        # Reduce over the last axis (time / horizon)
        total_cost = tf.reduce_sum(cost, axis=-1)
        total_demand = tf.reduce_sum(y_true_f, axis=-1)

        # Avoid division by zero by clamping with epsilon
        eps = tf.keras.backend.epsilon()
        total_demand_safe = tf.maximum(total_demand, eps)

        return total_cost / total_demand_safe

    return cwsl_loss
