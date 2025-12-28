"""Utility discovery for plex-leon.

This module provides functionality to automatically discover all BaseUtility
subclasses from the utils package without hardcoding them.
"""
from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plex_leon.utils.base_utility import BaseUtility


def discover_utilities() -> dict[str, type[BaseUtility]]:
    """Dynamically discover all BaseUtility subclasses from the utils package.

    This function imports all modules in the utils package and finds all
    classes that inherit from BaseUtility, creating a mapping from command
    names to utility classes.

    Returns:
        Dictionary mapping command names to utility classes
    """
    from plex_leon.utils.base_utility import BaseUtility
    import plex_leon.utils

    utilities = {}

    # Get the path to the utils package
    utils_path = plex_leon.utils.__path__

    # Iterate through all modules in the utils package
    for _, module_name, ispkg in pkgutil.iter_modules(utils_path):
        # Skip private modules, packages, and the base_utility module itself
        if module_name.startswith('_') or ispkg or module_name == 'base_utility':
            continue

        try:
            # Import the module
            module = importlib.import_module(f'plex_leon.utils.{module_name}')

            # Find all classes in the module that are subclasses of BaseUtility
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # Check if it's a class and a subclass of BaseUtility (but not BaseUtility itself)
                if (isinstance(attr, type) and
                    issubclass(attr, BaseUtility) and
                        attr is not BaseUtility):

                    # Get the command name from the class attribute
                    try:
                        command_name = attr.command
                        utilities[command_name] = attr
                    except AttributeError:
                        # Skip utilities that don't have a command attribute defined
                        pass

        except (ImportError, AttributeError):
            # Skip modules that can't be imported or don't have the expected structure
            continue

    return utilities
