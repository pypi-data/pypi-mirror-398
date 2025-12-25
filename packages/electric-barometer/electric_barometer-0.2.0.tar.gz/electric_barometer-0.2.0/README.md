# Electric Barometer

![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)
![Python Versions](https://img.shields.io/badge/Python-3.10%2B-blue)
![Project Status](https://img.shields.io/badge/Status-Alpha-yellow)

**Electric Barometer** is a modular, cost-aware forecasting evaluation framework designed
for operational decision-making. It provides a structured way to evaluate, compare, and
select forecasts when error costs are asymmetric and operational consequences matter.

Rather than delivering a single monolithic library, Electric Barometer is intentionally
organized as a small ecosystem of focused packages, each with a clear responsibility.

This repository serves as the **umbrella distribution and conceptual entry point** for
the Electric Barometer ecosystem.

---

## The Electric Barometer Ecosystem

Electric Barometer is composed of several interoperable packages:

- **`eb-metrics`**  
  Defines individual forecast error and service metrics, including cost-asymmetric
  measures such as Cost-Weighted Service Loss (CWSL), Forecast Readiness Score (FRS),
  and related primitives.

- **`eb-evaluation`**  
  Provides DataFrame-first utilities for applying metrics across entities, groups,
  hierarchies, and time windows. This layer handles evaluation, comparison, and
  selection logic while delegating metric math to `eb-metrics`.

- **`eb-adapters`**  
  Normalizes interfaces for external forecasting and regression libraries so they can
  be evaluated consistently. Adapters expose a common `.fit / .predict` contract for
  heterogeneous models.

- **`eb-examples`**  
  Contains worked examples, notebooks, and practical demonstrations showing how the
  Electric Barometer ecosystem is used end-to-end in real scenarios.

- **`eb-papers`**  
  The source of truth for conceptual definitions, theoretical foundations, and
  methodological rationale behind Electric Barometer metrics and frameworks.

Each package is versioned, tested, and documented independently, but designed to work
together seamlessly.

---

## What This Repository Provides

This `electric-barometer` repository:

- Acts as the **canonical entry point** to the ecosystem
- Provides a single install surface for core Electric Barometer functionality
- Establishes the conceptual map of the project
- Ensures compatible dependency resolution across subpackages

It intentionally contains minimal implementation code.

---

## Installation

Install the Electric Barometer umbrella package via pip:

```bash
pip install electric-barometer
```

This installs the core dependencies required to work with Electric Barometer metrics.
Additional functionality is provided by installing the underlying packages directly
(e.g., `eb-evaluation`, `eb-adapters`) or via future optional extras.

For development:

```bash
pip install -e .
```

---

## Design Philosophy

Electric Barometer is built around a few core principles:

- **Separation of concerns**  
  Metric definitions, evaluation logic, and model interfaces live in separate packages.

- **Cost-aware evaluation**  
  Forecast accuracy is evaluated in terms of operational impact, not symmetric error
  alone.

- **Operational realism**  
  Metrics and frameworks are designed for environments where underbuild and overbuild
  have different consequences.

- **Composable tooling**  
  Users can adopt only the layers they need without committing to a monolith.

---

## Examples and Tutorials

Examples, notebooks, and applied workflows are maintained in the separate
**`eb-examples`** repository.

This repository intentionally avoids embedding example code to keep the core packages
lean and focused.

---

## Documentation

Unified documentation for the Electric Barometer ecosystem is available at:

https://economistician.github.io/eb-docs/

Documentation is generated directly from source code docstrings and kept consistent
across packages.

---

## Status

Electric Barometer is under active development.
Public APIs may evolve prior to the first stable release.

---

## Authorship and Stewardship

The Electric Barometer ecosystem is designed and maintained by  
**Kyle Corrie** under the *Economistician* moniker.

The project reflects applied research and production experience in
forecasting, operations research, and cost-asymmetric decision systems
within large-scale operational environments.

For questions, collaboration, or research inquiries:

- GitHub: https://github.com/Economistician
- Contact: kcorrie@economistician.com

Conceptual foundations and formal methodology are documented in the
companion research repository **eb-papers**.

---

## License

This project is licensed under the BSD 3-Clause License.