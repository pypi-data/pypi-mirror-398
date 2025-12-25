# Electric Barometer Metrics (`eb-metrics`)

![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)
![Python Versions](https://img.shields.io/badge/Python-3.10%2B-blue)
[![Docs](https://img.shields.io/badge/docs-electric--barometer-blue)](https://economistician.github.io/eb-docs/)
![Project Status](https://img.shields.io/badge/Status-Alpha-yellow)

This repository contains the **reference Python implementation** of core metrics
defined within the *Electric Barometer* research program.

`eb-metrics` provides operationally meaningful forecasting metrics designed to
support readiness-oriented evaluation under asymmetric cost, service constraints,
and deployment considerations.

Formal definitions, theoretical motivation, and conceptual framing for these
metrics are maintained in the companion research repository:
**`eb-papers`**.

---

## Naming convention

Electric Barometer packages follow standard Python packaging conventions:

- **Distribution names** (used with `pip install`) use hyphens  
  e.g. `pip install eb-metrics`
- **Python import paths** use underscores  
  e.g. `import eb_metrics`

This distinction is intentional and consistent across the Electric Barometer
ecosystem.

---

## What This Library Provides

- **Asymmetric, cost-weighted loss metrics** (e.g., Cost-Weighted Service Loss)
- **Service-level and readiness diagnostics** (NSL, UD, HR@τ, FRS)
- **Classical regression metrics** for baseline comparison and diagnostics
- **Cost-ratio and sensitivity utilities** for asymmetric evaluation
- **Framework integrations** for TensorFlow / Keras and scikit-learn

The library is lightweight, dependency-minimal, and fully unit-tested.

---

## Scope

This repository focuses on **metric implementation**, not conceptual exposition.

**In scope:**
- Executable implementations of Electric Barometer metrics
- Consistent, validated APIs for loss and service evaluation
- Integration layers for common ML frameworks

**Out of scope:**
- Theoretical derivations and proofs
- Governance or managerial frameworks
- Empirical benchmarking studies
- End-user tutorials

---

## Installation

Once published, the package will be installable via PyPI:

```bash
pip install eb-metrics
```

For development or local use:

```bash
pip install -e .
```

---

## Quick Usage Example

```python
from eb_metrics.metrics.loss import cost_weighted_service_loss

loss = cost_weighted_service_loss(
    y_true=actual,
    y_pred=forecast,
    cost_ratio=R,
)
```

Examples are illustrative; consult function docstrings for full parameter
definitions and return semantics.

---

## Public API Overview

The primary public modules are:

- `eb_metrics.metrics.loss`  
  Asymmetric loss formulations (e.g., CWSL)

- `eb_metrics.metrics.service`  
  Service-level and readiness diagnostics (NSL, UD, HR@τ, FRS)

- `eb_metrics.metrics.regression`  
  Classical regression metrics

- `eb_metrics.metrics.cost_ratio`  
  Cost-ratio estimation and sensitivity utilities

- `eb_metrics.frameworks.keras_loss`  
  Keras-compatible loss wrappers

- `eb_metrics.frameworks.sklearn_scorer`  
  scikit-learn-compatible scoring interfaces

Users are encouraged to import from these modules rather than internal helpers.

---

## Conventions

Electric Barometer metrics follow consistent operational conventions, including:

- Explicit distinction between underbuild and overbuild
- Asymmetric cost ratios expressed as \(R = c_u / c_o\)
- Normalization relative to realized demand where applicable
- Clear directionality (e.g., lower loss indicates better performance)

Detailed semantic conventions are documented separately.

---

## Development and Testing

Tests are located under the `tests/` directory and mirror the package structure.

To run tests:

```bash
pytest
```

Contributions should preserve alignment with definitions in `eb-papers`.

---

## Relationship to Other EB Repositories

- `eb-papers`  
  Source of truth for conceptual definitions and evaluation philosophy.

- `eb-metrics`  
  Provides the metric implementations used during evaluation.

- `eb-evaluation`  
  Orchestrates evaluation workflows using adapted models.

- `eb-adapters`  
  Ensures heterogeneous models can be evaluated consistently.

When discrepancies arise, conceptual intent in `eb-papers` should be treated as authoritative.

---

## Status

This package is under active development.
Public APIs may evolve prior to the first stable release.
