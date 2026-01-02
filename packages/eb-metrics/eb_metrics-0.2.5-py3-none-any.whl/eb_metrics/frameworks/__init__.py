"""
Framework integrations for Electric Barometer metrics.

The ``eb_metrics.frameworks`` package provides **optional adapters** that allow
Electric Barometer metrics to plug into common machine-learning and forecasting
workflows (training, model selection, and evaluation) without redefining metric
semantics.

Currently supported integrations include:

- **scikit-learn** scorers (for model selection utilities such as ``GridSearchCV``)
- **Keras / TensorFlow** loss functions (for training deep learning models)

Notes
-----
- These integrations are thin wrappers around core Electric Barometer metrics.
  Metric definitions live in :mod:`eb_metrics.metrics`.
- Some integrations rely on optional third-party dependencies and may import
  those dependencies lazily (e.g., TensorFlow).

Conceptual definitions and interpretation are documented in the companion
research repository (`eb-papers`).
"""

# Keras / TensorFlow
from .keras_loss import make_cwsl_keras_loss

# scikit-learn
from .sklearn_scorer import cwsl_loss, cwsl_scorer

__all__ = [
    "cwsl_loss",
    "cwsl_scorer",
    "make_cwsl_keras_loss",
]
