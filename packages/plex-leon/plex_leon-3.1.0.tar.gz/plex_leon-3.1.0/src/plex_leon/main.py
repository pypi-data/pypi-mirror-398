from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from typing import TYPE_CHECKING

from plex_leon.shared import assert_required_tools_installed
from plex_leon.shared.utility_discovery import discover_utilities
from plex_leon.cli import help as help_module
from plex_leon.cli import menu as menu_module

if TYPE_CHECKING:
    # Import for type checking only; avoids importing runtime deps like loguru
    from plex_leon.utils.base_utility import BaseUtility


def _run_utility_with_timing(utility: 'BaseUtility', result_label: str, *args, **kwargs) -> int:
    """Run a utility with timing and print results.

    Args:
        utility: The utility instance to run
        result_label: Label for the result count (e.g., "Season folders renamed", "Episodes processed")
        *args: Positional arguments to pass to utility.process()
        **kwargs: Keyword arguments to pass to utility.process()

    Returns:
        Exit code (0 for success)
    """
    t0 = time.perf_counter()
    result = utility.process(*args, **kwargs)
    dt = time.perf_counter() - t0

    # Handle different return types (tuple or single value)
    if isinstance(result, tuple):
        if len(result) == 1:
            count = result[0]
            print(f"Done. {result_label}: {count}. Took {dt:.2f}s.")
        elif len(result) == 2:
            # Special case for migrate which returns (moved, skipped)
            moved, skipped = result
            if moved or skipped:
                print(
                    f"Done. Eligible files/folders moved: {moved}; skipped: {skipped}. Took {dt:.2f}s.")
    else:
        print(f"Done. {result_label}: {result}. Took {dt:.2f}s.")

    return 0


def _add_help_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "help",
        help="Show detailed help for a specific command",
        description="Display detailed information about available commands.",
    )
    p.add_argument(
        "subcommand",
        nargs="?",
        help="Command to show help for (e.g., 'migrate', 'season-renamer')",
    )
    return p


def _add_menu_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "menu",
        help="Interactive menu to pick and run a subcommand",
        description="Interactive menu to select a command and provide its arguments.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    # Discover all available utilities dynamically
    utilities = discover_utilities()

    # Build top-level parser with subcommands
    parser = argparse.ArgumentParser(
        prog="plex-leon",
        description="Utilities for managing media libraries based on TVDB IDs.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Build a mapping of command names to utility classes
    command_map = {}
    for command_name, utility_class in utilities.items():
        utility_class.add_parser(subparsers)
        command_map[command_name] = utility_class

    # Add non-utility commands
    _add_help_parser(subparsers)
    _add_menu_parser(subparsers)

    # Prepare argv: if argv is provided and its first element is a program name, drop it.
    if argv is None:
        parsed_argv = sys.argv[1:]
    else:
        parsed_argv = list(argv)

    # Get valid command names (dynamically from discovered utilities plus help)
    valid_commands = set(command_map.keys()) | {"help", "menu"}

    if parsed_argv and not parsed_argv[0].startswith("-") and parsed_argv[0] not in valid_commands:
        # Drop program name
        parsed_argv = parsed_argv[1:]

    args = parser.parse_args(parsed_argv)

    # If no subcommand was provided, default to the interactive menu
    # This makes calling `plex-leon` without a subcommand open the menu.
    if getattr(args, "command", None) is None:
        args.command = "menu"

    # Handle utility commands dynamically
    if args.command in command_map:
        utility_class = command_map[args.command]

        # Check required tools if needed
        if utility_class.requires_tools_check:
            try:
                assert_required_tools_installed()
            except RuntimeError as exc:
                print(f"❌ ERROR: {exc}")
                return 2

        # Create utility instance
        util = utility_class(dry_run=getattr(args, 'dry_run', False))

        # Get the result label from the utility instance
        result_label = util.result_label

        # Get process arguments from the utility class
        pos_args, kwargs = utility_class.prepare_process_args(args)

        return _run_utility_with_timing(util, result_label, *pos_args, **kwargs)

    # Handle non-utility commands
    if args.command == "help":
        return help_module.main(args.subcommand)

    if args.command == "menu":
        # Launch the interactive menu which handles prompting and execution.
        return menu_module.main()

    # No command provided
    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
