"""
Smoke tests for the Electric Barometer ecosystem.

Validates that required core packages import cleanly and that optional
ecosystem packages do not introduce import-time failures when present.
"""

import importlib
import importlib.util


def _can_import(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def test_smoke_imports_and_public_surface():
    # Required core packages
    import electric_barometer as eb

    # Minimal public-surface assertion for the flagship package
    assert hasattr(eb, "__version__")

    # Optional ecosystem packages
    optional = [
        "eb_evaluation",
        "eb_adapters",
        "eb_features",
    ]

    for name in optional:
        if _can_import(name):
            importlib.import_module(name)
