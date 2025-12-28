from __future__ import annotations

import os
from pathlib import Path
from typing import List

from plex_leon.shared import (
    get_season_number_from_dirname,
    unique_swap_path,
    merge_directory_contents,
    remove_dir_if_empty,
)
from plex_leon.utils.base_utility import BaseUtility, ParameterInfo


class SeasonRenamerUtility(BaseUtility):
    """Utility that normalises season folder names under a given library."""

    command = "season-renamer"
    brief_description = "Rename season folders like 'season 01' or 'Staffel 01' to 'Season 01'"
    result_label = "Season folders renamed"
    parameters = [
        ParameterInfo(
            name="--lib",
            required=False,
            description="Path to the library to process",
            default="./data/library-s"
        ),
        ParameterInfo(
            name="--dry-run",
            required=False,
            description="Show planned renames without changing the filesystem",
            default=False
        ),
    ]

    def process(self, library: Path | None = None) -> tuple[int]:
        if library is None:
            library = Path("data/library-s")
        if not isinstance(library, Path):
            library = Path(library)

        for dirpath, dirnames, _ in os.walk(library):
            # Work on a copy so we can safely update dirnames for os.walk
            for d in list(dirnames):
                old_path = Path(dirpath) / d
                if not old_path.is_dir():
                    continue
                # Skip top-level show folders directly under the library root
                # (only their subfolders should be treated as season folders)
                if Path(dirpath).resolve() == Path(library).resolve():
                    continue
                num = get_season_number_from_dirname(d)
                if num is None:
                    continue
                new_name = f"Season {num:02d}"
                new_path = Path(dirpath) / new_name

                # Already canonical
                if d == new_name:
                    continue

                # Case-only path: season 01 -> .plexleon_swap_Season 01 -> Season 01
                if d.lower() == new_name.lower():
                    # Find a unique swap path
                    swap_path = unique_swap_path(Path(dirpath), new_name)
                    show = Path(dirpath).name

                    if self.dry_run:
                        self.log_info(f"RENAME: {old_path} -> {swap_path}")
                        if new_path.exists():
                            self.log_info(f"MERGE: {swap_path} -> {new_path}")
                        else:
                            self.log_info(f"RENAME: {swap_path} -> {new_path}")
                        self.increment_stat(show, "RENAMED")
                        # Reflect rename so os.walk doesn't traverse old name
                        try:
                            idx = dirnames.index(d)
                            dirnames[idx] = new_name
                        except ValueError:
                            pass
                        continue

                    try:
                        # First hop: to swap
                        old_path.rename(swap_path)

                        # Second hop or merge
                        if not new_path.exists():
                            swap_path.rename(new_path)
                        else:
                            merge_directory_contents(swap_path, new_path)
                            # Try to remove empty swap
                            if not remove_dir_if_empty(swap_path):
                                # Best-effort warn
                                self.log_warning(
                                    f"failed to remove swap dir: {swap_path}")

                        # Reflect rename
                        try:
                            idx = dirnames.index(d)
                            dirnames[idx] = new_name
                        except ValueError:
                            pass
                        self.increment_stat(show, "RENAMED")
                    except OSError as e:
                        self.log_error(
                            f"two-step rename failed {old_path} -> {new_path}: {e}")
                        self.increment_stat(show, "ERRORS")
                    continue

                # Non-case-only path: direct rename when target doesn't exist; else skip.
                if new_path.exists():
                    self.log_warning(f"SKIP exists: {new_path}")
                    show = Path(dirpath).name
                    self.increment_stat(show, "SKIPPED")
                    continue

                if self.dry_run:
                    self.log_info(f"RENAME: {old_path} -> {new_path}")
                    show = Path(dirpath).name
                    self.increment_stat(show, "RENAMED")
                    try:
                        idx = dirnames.index(d)
                        dirnames[idx] = new_name
                    except ValueError:
                        pass
                    continue

                try:
                    old_path.rename(new_path)
                    try:
                        idx = dirnames.index(d)
                        dirnames[idx] = new_name
                    except ValueError:
                        pass
                    show = Path(dirpath).name
                    self.increment_stat(show, "RENAMED")
                except OSError as e:
                    self.log_error(
                        f"failed to rename {old_path} -> {new_path}: {e}")
                    show = Path(dirpath).name
                    self.increment_stat(show, "ERRORS")

        self.log_statistics("table")

        total_errors = sum(
            stats.get("ERRORS", 0) for stats in self.statistics.values()
        )
        if total_errors:
            self.log_error(
                f"{total_errors} season folder(s) failed to rename; see above for details.")

        total_renamed = sum(
            stats.get("RENAMED", 0) for stats in self.statistics.values()
        )

        return (total_renamed,)
