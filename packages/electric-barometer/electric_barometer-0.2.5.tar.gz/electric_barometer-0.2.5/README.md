# Electric Barometer (`electric-barometer`)

[![CI](https://github.com/Economistician/electric-barometer/actions/workflows/ci.yml/badge.svg)](https://github.com/Economistician/electric-barometer/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/License-BSD--3--Clause-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
[![PyPI version](https://img.shields.io/pypi/v/electric-barometer.svg)](https://pypi.org/project/electric-barometer/)

Top-level orchestration and entry-point package for the Electric Barometer ecosystem.

---

## Overview

Electric Barometer is a modular framework for evaluating and selecting forecasts in operational environments where traditional accuracy metrics are insufficient. Rather than focusing solely on statistical error, the framework emphasizes service risk, asymmetry, and execution readiness.

This repository serves as the top-level entry point for the Electric Barometer ecosystem. It establishes a stable system boundary and coordinates access to core components. Detailed implementations of metrics, evaluation workflows, feature engineering utilities, and integration adapters live in dedicated sub-packages.

---

## Role in the Electric Barometer Ecosystem

`electric-barometer` defines the public system boundary for the Electric Barometer ecosystem. It provides a unified entry point, establishes compatible dependency constraints across core packages, and ensures that the ecosystem can be installed and imported as a coherent whole.

This repository does not implement metrics, evaluation logic, feature engineering, or model adapters directly. Those responsibilities live in dedicated sub-packages. Instead, this layer coordinates composition, versioning, and optional integration, allowing users to adopt only the components they need while maintaining a stable and well-defined top-level interface.

---

## Installation

```bash
pip install electric-barometer
```

---

## Design Philosophy

Electric Barometer is designed around the idea that forecast quality in operational systems cannot be reduced to a single notion of statistical accuracy. In many real-world settings, the cost of over-forecasting and under-forecasting is asymmetric, and the consequences of failure depend on execution constraints rather than abstract error alone.

The ecosystem is intentionally modular. Metrics, evaluation workflows, feature
engineering utilities, and integration adapters are developed as independent components with clear responsibilities. This separation allows the framework to remain flexible, composable, and adaptable to different operational contexts without forcing a monolithic workflow.

At the system level, Electric Barometer prioritizes explicit contracts, stable interfaces, and conservative composition. The top-level orchestration layer exists to define clear boundaries and reduce coupling, ensuring that the ecosystem can evolve without breaking downstream usage.

---

## License

BSD 3-Clause License.  
© 2025 Kyle Corrie.