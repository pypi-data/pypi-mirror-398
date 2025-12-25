from __future__ import annotations

"""
electric-barometer
==================

Umbrella package for the Electric Barometer ecosystem.

This distribution intentionally contains minimal runtime code. Its primary
purpose is to provide a stable installation and versioning surface for the
Electric Barometer framework by coordinating the following leaf packages:

- eb-metrics     : Core asymmetric forecast metrics
- eb-fevaluation : DataFrame-based evaluation and orchestration utilities
- eb-features    : Panel and time-series feature engineering utilities
- eb-adapters    : Forecast model adapter interfaces

End users are expected to interact primarily with the leaf packages directly.
"""

from importlib.metadata import PackageNotFoundError, version


def _resolve_version() -> str:
    """Resolve the installed version of the electric-barometer distribution."""
    try:
        return version("electric-barometer")
    except PackageNotFoundError:
        # Fallback for editable installs or source checkouts
        return "0.0.0"


__version__ = _resolve_version()

__all__ = ["__version__"]