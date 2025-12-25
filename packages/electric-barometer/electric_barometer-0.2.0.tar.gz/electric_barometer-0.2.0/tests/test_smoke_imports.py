import importlib


def _can_import(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def test_smoke_imports():
    import electric_barometer  # noqa: F401
    import eb_metrics  # noqa: F401

    # Optional ecosystem packages (may not be installed yet)
    if _can_import("eb_evaluation"):
        import eb_evaluation  # noqa: F401
    if _can_import("eb_adapters"):
        import eb_adapters  # noqa: F401