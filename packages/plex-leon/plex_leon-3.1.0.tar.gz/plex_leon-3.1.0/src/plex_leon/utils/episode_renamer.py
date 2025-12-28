from __future__ import annotations

import os
from pathlib import Path
from typing import List

from plex_leon.shared import (
    strip_tvdb_suffix,
    normalize_episode_tag,
    is_season_like_dirname,
    two_step_case_rename,
)
from plex_leon.utils.base_utility import BaseUtility, ParameterInfo


class EpisodeRenamerUtility(BaseUtility):
    """Class wrapper for episode renaming that exposes `process()` using the
    BaseUtility logging helpers.

    Example:
        EpisodeRenamerUtility(dry_run=True).run(library)
    """

    command = "episode-renamer"
    brief_description = "Rename episode files to '<Show (Year)> - sNNeMM[ -ePP].ext' using the show folder name."
    result_label = "Episode files renamed"
    parameters = [
        ParameterInfo(
            name="--lib",
            required=False,
            description="Path to the library to process",
            default="./data/library-e"
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
            library = Path("data/library-e")
        if not isinstance(library, Path):
            library = Path(library)

        for dirpath, _, filenames in os.walk(library):
            parent = Path(dirpath)
            for fn in filenames:
                if fn.startswith('.'):
                    continue
                old_path = parent / fn
                se_tag = normalize_episode_tag(fn)
                if not se_tag:
                    continue

                # Expect structure: <lib>/<Show Folder>/Season XX/<file>
                # Fallback to the immediate parent's parent as show folder when available
                show_dir = parent.parent if is_season_like_dirname(
                    parent.name) else parent
                # If library root reached, skip
                if show_dir == library or show_dir.parent == show_dir:
                    continue
                show_title = strip_tvdb_suffix(show_dir.name)

                new_name = f"{show_title} - {se_tag}{old_path.suffix}"
                new_path = old_path.with_name(new_name)

                if old_path.name == new_name:
                    continue

                # Case-only change requires two-step rename
                if old_path.name.lower() == new_name.lower():
                    ok = two_step_case_rename(
                        old_path, new_path, dry_run=self.dry_run)
                    if ok:
                        self.increment_stat(show_title, "RENAMED")
                        suffix = " (dry-run)" if self.dry_run else ""
                        self.log_info(
                            f"✅ RENAMED (case-only): {old_path} -> {new_path}{suffix}")
                    continue

                # Non-case change: direct rename if destination doesn't exist
                if new_path.exists():
                    self.increment_stat(show_title, "SKIPPED")
                    self.log_warning(f"SKIP exists: {old_path} -> {new_path}")
                    continue

                if self.dry_run:
                    self.increment_stat(show_title, "RENAMED")
                    self.log_info(
                        f"RENAME (dry-run): {old_path} -> {new_path}")
                    continue

                try:
                    old_path.rename(new_path)
                    self.increment_stat(show_title, "RENAMED")
                    self.log_info(f"✅ RENAMED: {old_path} -> {new_path}")
                except OSError as e:
                    # log and count per-show
                    self.log_error(
                        f"failed to rename {old_path} -> {new_path}: {e}")
                    self.increment_stat(show_title, "ERRORS")

        self.log_statistics("table")

        total_errors = sum(
            stats.get("ERRORS", 0) for stats in self.statistics.values()
        )
        if total_errors:
            self.log_error(
                f"{total_errors} file(s) failed to rename; see above for details.")

        total_renamed = sum(
            stats.get("RENAMED", 0) for stats in self.statistics.values()
        )

        return (total_renamed,)
