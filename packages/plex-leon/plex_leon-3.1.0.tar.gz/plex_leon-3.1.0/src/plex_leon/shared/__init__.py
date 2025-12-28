import importlib
import pkgutil
import re
import ast
from pathlib import Path
from typing import Dict

# Additional regex/utilities for episode and folder handling
EPISODE_TAG_REGEX = re.compile(r"(?i)s(\d{1,2})e(\d{1,2})(?:-e(\d{1,2}))?")
TVDB_SUFFIX_REGEX = re.compile(r"\s*\{tvdb-\d+}\s*", re.IGNORECASE)
_SEASON_DIGITS_RE = re.compile(r"(\d+)")

# Compiled regex used to extract TVDB ids like "{tvdb-12345}" from filenames
TVDB_REGEX = re.compile(r"\{tvdb-(\d+)\}", re.IGNORECASE)

# Auto-discover available submodules in this package. We will lazily import
# symbols from these modules on first access to avoid circular imports and to
# keep import-time light.
_SUBMODULES = [
    name for _, name, ispkg in pkgutil.iter_modules(__path__) if not ispkg
]

# Build a mapping of exported symbol -> submodule name by statically
# analysing each submodule's source using the AST module. This avoids
# importing submodules during package import and preserves lazy semantics.
_EXPORTS: Dict[str, str] = {}
pkg_dir = Path(__path__[0])
for mod_name in _SUBMODULES:
    mod_file = pkg_dir / f"{mod_name}.py"
    if not mod_file.exists():
        continue
    try:
        src = mod_file.read_text(encoding="utf8")
        tree = ast.parse(src)
    except Exception:
        # If parsing fails, skip this module — errors will surface when the
        # symbol is actually accessed and the real import/parse occurs.
        continue

    # If module defines __all__, prefer those names. Otherwise collect
    # top-level function/class/assign names that don't start with an underscore.
    explicit_all = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    # Attempt to evaluate a literal list/tuple if present
                    try:
                        explicit_all = ast.literal_eval(node.value)
                    except Exception:
                        explicit_all = None
                    break
        if explicit_all is not None:
            break

    names = []
    if explicit_all:
        for n in explicit_all:
            if isinstance(n, str) and not n.startswith("_"):
                names.append(n)
    else:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    names.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if not name.startswith("_"):
                            names.append(name)

    for name in names:
        _EXPORTS.setdefault(name, mod_name)


def __getattr__(name: str):
    """Lazily import and return exported symbols from submodules.

    - Return constants defined in this module immediately.
    - Otherwise, find the submodule that provides `name`, import it, cache
      the attribute on this module, and return it.
    """
    # Return constants defined in this module immediately
    if name in globals():
        return globals()[name]

    mod_name = _EXPORTS.get(name)
    if mod_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = importlib.import_module(f"{__name__}.{mod_name}")
    value = getattr(mod, name)
    # Cache on module for subsequent access
    globals()[name] = value
    return value


def __dir__():
    return sorted(list(globals().keys()) + sorted(_EXPORTS.keys()))


__all__ = [
    "EPISODE_TAG_REGEX",
    "TVDB_SUFFIX_REGEX",
    "TVDB_REGEX",

] + sorted(_EXPORTS.keys())
