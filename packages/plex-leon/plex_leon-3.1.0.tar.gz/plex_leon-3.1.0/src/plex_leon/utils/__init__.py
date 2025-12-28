"""Utilities subpackage for plex_leon."""
import importlib
import pkgutil

__all__ = [
    name
    for _, name, ispkg in pkgutil.iter_modules(__path__)
    if not name.startswith("_") and not ispkg
]


def __getattr__(name):
    if name in __all__:
        mod = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = mod
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + __all__)
