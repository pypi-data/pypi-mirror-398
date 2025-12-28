from __future__ import annotations

from abc import ABC, abstractmethod
import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any
from typing import Union
from typing import Dict
from typing import List

from loguru import logger


@dataclass
class BaseOptions:
    dry_run: bool = False
    forced: bool = False
    # Accept numeric or human-readable log level (e.g. 20 or "info")
    log_level: Union[int, str] = 20  # similar to logging.INFO


@dataclass
class ParameterInfo:
    """Metadata for a command-line parameter."""
    name: str
    required: bool
    description: str
    default: Any = None


class BaseUtility(ABC):
    """Base class for utilities.

    Provides simple logging helpers and a run() entrypoint that calls the
    concrete implementation's process() method.

    Subclasses must define these class-level attributes:
    - command: str - The CLI command name (e.g., "migrate", "season-renamer")
    - brief_description: str - Short one-line description of what the utility does
    - parameters: List[ParameterInfo] - List of command-line parameters

    Subclasses and instances may collect operation statistics in the
    `statistics` attribute. Its shape is:

    {
            "Attack on Titan (2013)": {"RENAMED": 87, "SKIPPED": 0, "ERRORS": 0},
            "Classroom of the Elite (2017)": {"RENAMED": 38, "SKIPPED": 0, "ERRORS": 0},
    }

    Helper methods provided on this base class:

    - increment_stat(stat, step, value=1): increment a named step counter
        for the given category (creates nested mappings as necessary).
    - log_statistics(format): pretty-print collected statistics in either a
        compact table ("table") or per-category step list ("steps").
    """

    # Class-level metadata that subclasses must define
    command: str
    brief_description: str
    parameters: List[ParameterInfo]

    # Optional class-level metadata with defaults
    result_label: str = "Items processed"
    requires_tools_check: bool = False

    @classmethod
    def add_parser(cls, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """Create and add an argparse subparser for this utility.

        This method generates the parser configuration from the class metadata
        (command, brief_description, and parameters attributes).

        Args:
            subparsers: The argparse _SubParsersAction to add this parser to

        Returns:
            The created ArgumentParser for this utility
        """
        parser = subparsers.add_parser(
            cls.command,
            help=cls.brief_description,
            description=cls.brief_description,
        )

        # Add parameters from the metadata
        for param in cls.parameters:
            kwargs = {}

            # Set the type based on default value
            if param.default is not None:
                if isinstance(param.default, bool):
                    kwargs["action"] = "store_true"
                elif isinstance(param.default, Path):
                    kwargs["type"] = Path
                    kwargs["default"] = param.default
                elif isinstance(param.default, int):
                    kwargs["type"] = int
                    kwargs["default"] = param.default
                else:
                    kwargs["default"] = param.default

            # Add help text
            help_text = param.description
            if param.default is not None and not isinstance(param.default, bool):
                help_text += f" (default: {param.default})"
            kwargs["help"] = help_text

            parser.add_argument(param.name, **kwargs)

        return parser

    @classmethod
    def prepare_process_args(cls, args: argparse.Namespace) -> tuple[tuple, dict]:
        """Convert argparse Namespace to arguments for process() method.

        Subclasses can override this method to customize how argparse arguments
        are mapped to process() method parameters.

        The default implementation handles common patterns:
        - If 'lib' is present, it's passed as the first positional argument
        - Arguments like 'command' and 'dry_run' are excluded (dry_run is handled by constructor)
        - All other arguments are passed as kwargs

        Args:
            args: The argparse Namespace containing parsed command-line arguments

        Returns:
            A tuple of (positional_args, keyword_args) to pass to process()
        """
        args_dict = vars(args)
        excluded_keys = {'command', 'dry_run'}

        # Check if 'lib' is present and should be a positional argument
        if 'lib' in args_dict:
            positional = (args_dict['lib'],)
            kwargs = {k: v for k, v in args_dict.items()
                      if k not in (excluded_keys | {'lib'}) and v is not None}
        else:
            # Pass all non-None arguments as kwargs (except excluded ones)
            positional = ()
            kwargs = {k: v for k, v in args_dict.items()
                      if k not in excluded_keys and v is not None}

        # statistics is a mapping of category -> (mapping of step -> count)
        return positional, kwargs
    statistics: Dict[str, Dict[str, int]]

    def __init__(self, *, dry_run: bool = False, forced: bool = False, log_level: Union[int, str] = 20) -> None:
        self.opts = BaseOptions(
            dry_run=dry_run, forced=forced, log_level=log_level)

        self.statistics = {}

        # Configure loguru once per process. The first BaseUtility created
        # will set a stderr sink with the provided level. Subsequent
        # instances won't add duplicate sinks.
        if not getattr(logger, "_plex_leon_configured", False):
            logger.remove()

            # normalize the level (accept strings like "debug", "INFO", or numeric values)
            level = self._normalize_level(self.log_level)

            # Use a compact format that omits module/function/line to keep logs
            # focused on timestamp, level and the message. Messages already
            # include the visual emoji prefixes from the helpers (ℹ️, ⚠️, ❌).
            fmt = (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | {message}"
            )
            logger.add(sys.stderr, level=level, format=fmt)
            setattr(logger, "_plex_leon_configured", True)

    # Convenience properties
    @property
    def dry_run(self) -> bool:
        return self.opts.dry_run

    @property
    def forced(self) -> bool:
        return self.opts.forced

    @property
    def log_level(self) -> int:
        return self.opts.log_level

    def _normalize_level(self, level: int | str) -> int | str:
        """Normalize a human-friendly level to something loguru accepts.

        Accepts numeric levels (passed through) or common strings like
        'debug', 'INFO', 'Trace', etc. Returns either an int or upper-case
        level name string that loguru accepts.
        """
        if isinstance(level, int):
            return level
        if not isinstance(level, str):
            raise TypeError("log_level must be int or str")
        name = level.strip().upper()
        mapping = {
            "TRACE": "TRACE",
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "SUCCESS": "SUCCESS",
            "WARNING": "WARNING",
            "WARN": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
            "FATAL": "CRITICAL",
        }
        return mapping.get(name, name)

    def log_error(self, msg: str, /) -> None:
        logger.error(f"❌ ERROR: {msg}")

    def log_warning(self, msg: str, /) -> None:
        logger.warning(f"⚠️ WARN: {msg}")

    def log_info(self, msg: str, /) -> None:
        logger.info(f"ℹ️ {msg}")

    def log_debug(self, msg: str, /) -> None:
        logger.debug(f"🐛 DEBUG: {msg}")

    def log_verbose(self, msg: str, /) -> None:
        logger.trace(f"🔍 VERBOSE: {msg}")

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the utility.

        Delegates to the concrete process() implementation. Subclasses must
        implement process(). The run method provides a stable entrypoint and
        ensures dry-run option is available on the instance.
        """
        try:
            return self.process(*args, **kwargs)
        except Exception as e:
            self.log_error(str(e))
            raise

    def increment_stat(self, stat: str, step: str, value: int = 1) -> None:
        """Increment the statistic for a category and step.

        Args:
            stat: category name (e.g. "Attack on Titan (2013)")
            step: step name (e.g. "RENAMED", "SKIPPED", "ERRORS")
            value: amount to add (defaults to 1)
        """
        if not isinstance(value, int):
            raise TypeError("value must be an int")

        cat = self.statistics.setdefault(stat, {})
        cat[step] = cat.get(step, 0) + value

    def log_statistics(self, format: str = "table") -> None:
        """Log collected statistics in either 'table' or 'steps' format.

        - 'table': prints a compact table with columns for each step.
        - 'steps': prints each category followed by step lines.
        """
        if format not in ("table", "steps"):
            raise ValueError("format must be 'table' or 'steps'")

        if not self.statistics:
            self.log_info("No statistics to show.")
            return

        # collect all steps present across categories to construct columns
        all_steps = set()
        for cat_map in self.statistics.values():
            all_steps.update(cat_map.keys())

        # deterministic ordering
        steps = sorted(all_steps)

        if format == "steps":
            for category, cat_map in sorted(self.statistics.items()):
                self.log_info(f"{category}")
                for step in steps:
                    val = cat_map.get(step, 0)
                    # match example spacing: ' - RENAMED:  87 '
                    self.log_info(f" - {step}: {val} ")
            return

        # format == 'table'
        # compute column widths
        cat_col = "Category"
        col_widths = [max(len(cat_col), max((len(c)
                          for c in self.statistics.keys()), default=0))]
        for step in steps:
            # width should accommodate step name and numbers
            max_num_width = max((len(str(self.statistics.get(c, {}).get(
                step, 0))) for c in self.statistics.keys()), default=0)
            col_widths.append(max(len(step), max_num_width))

        # header
        header_cols = [cat_col] + steps
        header = " | ".join(h.ljust(w)
                            for h, w in zip(header_cols, col_widths))
        self.log_info(header)

        # rows
        for category in sorted(self.statistics.keys()):
            row = [category.ljust(col_widths[0])]
            cat_map = self.statistics.get(category, {})
            for i, step in enumerate(steps, start=1):
                row.append(str(cat_map.get(step, 0)).rjust(col_widths[i]))
            self.log_info(" | ".join(row))

    @abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()
