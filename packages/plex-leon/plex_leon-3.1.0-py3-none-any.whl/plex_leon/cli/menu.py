"""Interactive menu for plex-leon utilities.

Allows the user to pick a discovered subcommand and then prompts for its
arguments dynamically using the `ParameterInfo` metadata provided by each
utility class. Nothing is hardcoded: parameter names, labels and defaults are
read directly from the utility classes.
"""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from plex_leon.utils.base_utility import BaseUtility, ParameterInfo

from plex_leon.shared.utility_discovery import discover_utilities


def _friendly_attr_name(param_name: str) -> str:
    """Convert argparse-style name (e.g. '--lib-a') to attribute name ('lib_a')."""
    return param_name.lstrip('-').replace('-', '_')


def _coerce_value(default: Any, raw: str) -> Any:
    """Coerce the raw input string into an appropriate python value using the default as hint.

    If default is a bool, treat as yes/no. If default is a Path, return Path(raw).
    If default is an int, cast to int. If default is None, return the raw string.
    Empty raw strings return None (caller may enforce requiredness).
    """
    if raw == "":
        return None

    # Infer type from default when possible
    if isinstance(default, bool):
        lowered = raw.strip().lower()
        if lowered in ("y", "yes", "true", "1"):
            return True
        if lowered in ("n", "no", "false", "0"):
            return False
        # fallback: truthy
        return bool(lowered)

    if isinstance(default, Path):
        return Path(raw)

    if isinstance(default, int):
        try:
            return int(raw)
        except ValueError:
            # Let caller handle invalid input; return raw
            return raw

    # No good hint: return raw string
    return raw


def _prompt_for_param(param: "ParameterInfo") -> Any:
    """Prompt the user for a single parameter and return the coerced value.

    Uses the ParameterInfo.description and default to build a helpful prompt.
    """
    attr = _friendly_attr_name(param.name)
    prompt_label = f"{param.name} ({param.description})"

    # For boolean flags, show [y/N] style; for others show default if present.
    if isinstance(param.default, bool):
        default_label = "Y/n" if param.default else "y/N"
        while True:
            raw = input(f"{prompt_label} [{default_label}]: ").strip()
            if raw == "":
                return param.default
            val = _coerce_value(param.default, raw)
            # Must be boolean-like
            if isinstance(val, bool):
                return val
            print("Please answer 'y' or 'n'.")

    else:
        default_text = f" [default: {param.default}]" if param.default is not None else ""
        while True:
            raw = input(f"{prompt_label}{default_text}: ").strip()
            if raw == "":
                if param.required and param.default is None:
                    print("This parameter is required; please provide a value.")
                    continue
                return param.default
            coerced = _coerce_value(param.default, raw)
            return coerced


def _collect_arguments_for_utility(utility_class: type["BaseUtility"]) -> SimpleNamespace:
    """Collect arguments from the user for the given utility class.

    Returns an argparse-like Namespace (SimpleNamespace) with attributes named
    according to argparse's conversion (dashes -> underscores).
    """
    answers: dict[str, Any] = {}

    for param in utility_class.parameters:
        attr = _friendly_attr_name(param.name)
        val = _prompt_for_param(param)
        answers[attr] = val

    return SimpleNamespace(**answers)


def main() -> int:
    """Run the interactive menu.

    Returns exit code 0 on success or 1 on error.
    """
    utilities = discover_utilities()

    if not utilities:
        print("No utilities discovered.")
        return 1

    print("plex-leon - Interactive utility menu\n")

    # Present numbered list
    items = sorted(utilities.items())
    for idx, (cmd_name, ucls) in enumerate(items, start=1):
        try:
            brief = ucls.brief_description
        except AttributeError:
            brief = "(missing brief_description)"
        print(f"{idx:2d}) {cmd_name:20s} {brief}")

    print("\nEnter the number or command name to run, or 'q' to quit.")

    selection = input("Select command: ").strip()
    if selection.lower() in ("q", "quit", "exit"):
        print("Goodbye.")
        return 0

    # Resolve selection
    selected_class = None
    if selection.isdigit():
        i = int(selection) - 1
        if 0 <= i < len(items):
            selected_class = items[i][1]
    else:
        # try direct name lookup
        if selection in utilities:
            selected_class = utilities[selection]
        else:
            # try fuzzy match on command names
            matches = [cls for name,
                       cls in items if name.startswith(selection)]
            if len(matches) == 1:
                selected_class = matches[0]

    if selected_class is None:
        print("Invalid selection.")
        return 1

    # Collect args
    args_ns = _collect_arguments_for_utility(selected_class)

    # Extract constructor kwargs (dry_run/forced/log_level) if provided by params
    ctor_kwargs: dict[str, Any] = {}
    for k in ("dry_run", "forced", "log_level"):
        if hasattr(args_ns, k):
            ctor_kwargs[k] = getattr(args_ns, k)

    # Ensure defaults for ctor kwargs if not provided
    if 'dry_run' not in ctor_kwargs:
        ctor_kwargs['dry_run'] = False

    # Instantiate actual utility
    try:
        util = selected_class(**ctor_kwargs)
    except Exception as e:
        print(f"Failed to instantiate utility: {e}")
        return 1

    # Convert collected namespace to an argparse.Namespace-like object
    # so we can call prepare_process_args which expects argparse.Namespace
    import argparse
    args_for_prepare = argparse.Namespace(**vars(args_ns))

    try:
        positional, kwargs = selected_class.prepare_process_args(
            args_for_prepare)
    except Exception as e:
        print(f"Failed to prepare process args: {e}")
        return 1

    print("\nRunning utility...\n")
    try:
        result = util.run(*positional, **kwargs)
    except Exception as e:
        print(f"Utility raised an exception: {e}")
        return 1

    # Pretty-print result when possible
    try:
        label = util.result_label
    except Exception:
        label = "Result"

    print(f"\n{label}: {result}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
