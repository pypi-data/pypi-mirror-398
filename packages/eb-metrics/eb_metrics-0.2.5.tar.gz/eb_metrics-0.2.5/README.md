# Electric Barometer · Metrics (`eb-metrics`)

[![CI](https://github.com/Economistician/eb-metrics/actions/workflows/ci.yml/badge.svg)](https://github.com/Economistician/eb-metrics/actions/workflows/ci.yml)
![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)
![Python Versions](https://img.shields.io/pypi/pyversions/eb-metrics)
![PyPI](https://img.shields.io/pypi/v/eb-metrics)

Asymmetric, readiness-oriented forecast evaluation metrics for operational decision systems.

---

## Overview

`eb-metrics` provides a set of forecast evaluation metrics designed for operational environments where the consequences of error are asymmetric and interval-level reliability matters. Traditional accuracy measures such as RMSE or MAE treat overforecasting and underforecasting symmetrically and summarize average deviation, often obscuring whether a forecast is suitable for real-world
execution.

The metrics in this package evaluate forecasts in terms of service protection, shortfall behavior, and cost-weighted impact. They are designed for readiness-oriented assessment in settings such as production, staffing, inventory, logistics, and short-horizon demand planning, where even small shortfalls can create disproportionate operational disruption. `eb-metrics` serves as the foundational metric layer of the Electric Barometer ecosystem, providing interpretable primitives that support decision-aligned forecast comparison and selection.

---

## Role in the Electric Barometer Ecosystem

`eb-metrics` defines the core metric primitives used throughout the Electric Barometer ecosystem. It is responsible for implementing asymmetric loss, reliability, and readiness-oriented forecast evaluation measures in a form that is interpretable, composable, and operationally aligned.

This package focuses exclusively on metric definition and behavior. It does not manage data aggregation, evaluation workflows, model interfaces, feature construction, or integration testing. Those concerns are handled by adjacent layers in the ecosystem that apply, orchestrate, or consume these metrics in broader forecasting and decision-making pipelines.

By separating metric semantics from evaluation logic and execution concerns, `eb-metrics` provides a stable foundation that supports consistent, decision-aligned forecast assessment across heterogeneous operational contexts.

---

## Installation

`eb-metrics` is distributed as a standard Python package.

```bash
pip install eb-metrics
```

The package supports Python 3.10 and later.

---

## Core Concepts

- **Asymmetric error** — Overforecasting and underforecasting can have different operational consequences, so evaluation should reflect directional cost differences.
- **Interval reliability** — In readiness-oriented systems, it matters how often forecasts meet demand within each interval, not just average error over time.
- **Shortfall behavior** — Underbuilding events are operationally distinct; evaluation should capture both their frequency and their severity.
- **Tolerance-based adequacy** — Many systems can absorb small deviations; reliability can be expressed as the frequency of “accurate enough” intervals.
- **Readiness-oriented evaluation** — Forecast quality is assessed by execution feasibility and risk, not solely statistical deviation.

---

## Minimal Example

The following example computes Cost-Weighted Service Loss (CWSL) for a single demand series using asymmetric penalties for underbuild and overbuild:

```python
import numpy as np
from eb_metrics import cwsl

# Realized demand and corresponding forecast
y_true = np.array([20, 28, 32, 35, 40, 42])
y_pred = np.array([22, 25, 29, 36, 37, 45])

# Compute cost-weighted service loss
loss = cwsl(
    y_true=y_true,
    y_pred=y_pred,
    underbuild_cost=2.0,
    overbuild_cost=1.0,
)

print(loss)
```

---

## License

BSD 3-Clause License.  
© 2025 Kyle Corrie.