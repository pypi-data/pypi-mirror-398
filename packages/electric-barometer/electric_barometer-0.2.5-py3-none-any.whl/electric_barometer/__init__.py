"""
Top-level orchestration package for the Electric Barometer ecosystem.

This distribution intentionally contains minimal runtime code. Its primary purpose
is to provide a stable installation and versioning surface and to coordinate
compatible dependency constraints across the core Electric Barometer packages.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def _resolve_version() -> str:
    """Return the installed version of the electric-barometer distribution."""
    try:
        return version("electric-barometer")
    except PackageNotFoundError:
        # Not installed (e.g., running from a source checkout)
        return "0.0.0"


__version__ = _resolve_version()

__all__ = ["__version__"]
