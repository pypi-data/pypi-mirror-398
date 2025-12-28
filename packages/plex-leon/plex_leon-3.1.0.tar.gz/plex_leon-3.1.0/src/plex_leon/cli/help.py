"""Help system for plex-leon utilities.

This module provides a help command that displays detailed information about
available utilities by reading their metadata (command, brief_description, and
parameters) directly from the utility classes.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plex_leon.utils.base_utility import BaseUtility

from plex_leon.shared.utility_discovery import discover_utilities


def print_general_help() -> None:
    """Print general help listing all available commands."""
    utilities = discover_utilities()

    print("plex-leon - Utilities for managing media libraries based on TVDB IDs\n")
    print("Available commands:\n")

    for cmd_name, utility_class in utilities.items():
        print(f"  {cmd_name:20s} {utility_class.brief_description}")

    print("\nUse 'plex-leon help <command>' for detailed information about a specific command.")
    print("Use 'plex-leon <command> --help' to see argparse-generated help.")


def print_command_help(command: str) -> None:
    """Print detailed help for a specific command.

    Args:
        command: The command name (e.g., 'migrate', 'season-renamer')
    """
    utilities = discover_utilities()
    utility_class = utilities.get(command)

    if not utility_class:
        print(f"Unknown command: {command}")
        print(f"\nAvailable commands: {', '.join(utilities.keys())}")
        return

    print(f"Command: {utility_class.command}")
    print(f"\n{utility_class.brief_description}\n")

    if utility_class.parameters:
        print("Parameters:")
        for param in utility_class.parameters:
            required_marker = " (required)" if param.required else ""
            default_info = f" [default: {param.default}]" if param.default is not None and not param.required else ""
            print(f"  {param.name}{required_marker}")
            print(f"      {param.description}{default_info}")
        print()


def main(command: str | None = None) -> int:
    """Main entry point for the help system.

    Args:
        command: Optional command name to show help for. If None, shows general help.

    Returns:
        Exit code (0 for success)
    """
    if command:
        print_command_help(command)
    else:
        print_general_help()

    return 0
