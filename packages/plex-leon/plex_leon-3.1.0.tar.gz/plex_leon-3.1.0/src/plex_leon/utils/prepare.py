"""Library preparation utilities.

This module provides a `process` function that scans a *root* directory for
TV show folders and normalises episode placement & naming:

1. Detect show folders whose name matches the convention:
	  TV Show Name (YYYY) {tvdb-12345}
   (The year is a 4-digit number in parentheses; the TVDB id is in curly braces.)
2. Inside each show folder, locate loose episode media files (i.e. files that
   are direct children of the show directory, not already inside a canonical
   `Season NN` directory.)
3. Derive season & episode numbers from the filename. Supported patterns:
	  - Standard tags: S01E02, s1e2, S01E02-E03 (double episodes -> first used)
	  - German style:  "Episode 12 Staffel 2"  (episode first)
	  - German style:  "Staffel 2 Episode 12"  (season first)
   If none match, the file is skipped silently.
4. Create the target season directory named `Season NN` (NN zero-padded) if it
   does not already exist.
        5. Move & rename the file to:
            <Show Name (YYYY)> - sSSeEE.ext   (per spec: 's01e01')
     NOTE: The user requested the format `s01e01` (season then episode), which
     is the more common convention. The code uses this pattern for target
     filenames.
6. Case-only changes are applied via a two-step rename using the existing
   `two_step_case_rename` helper.

Returns a 1-tuple with the count of episode files moved/renamed.

Inspired by logic in `episode_renamer` & `season_renamer` modules.

Validation
----------
Before making any filesystem changes for a show, `process` runs a validation
step that checks each show folder for two common problems:

- Missing TVDB id in the folder name (the folder name must contain
    "{tvdb-<digits>}"), and
- Duplicate episode files for the same season/episode (e.g. two files that
    both parse as S01E05).

Any validation messages are printed. If validation reports any ERROR-level
problems for a show, the renaming and season-folder creation are skipped for
that show; WARN-level issues (unparseable filenames) are reported but are not
fatal by default.

Statistics
----------
This module records per-show statistics on the utility instance using the
`self.statistics` attribute (a mapping: Dict[str, Dict[str, int]]). Each key
is a show/category name (e.g. "Attack on Titan (2013)") and the inner mapping
contains step counts such as:

- "RENAMED": number of files moved/renamed for the show
- "SKIPPED": number of files skipped because the destination exists
- "ERRORS": number of errors encountered for the show

Recording is performed via `self.increment_stat(category, step, value)` and
summaries can be printed with `self.log_statistics(format)` where `format` is
either "table" or "steps".
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List

from plex_leon.shared import (
    two_step_case_rename,
    parse_episode_tag,
    strip_tvdb_suffix,
)
from plex_leon.utils.base_utility import BaseUtility, ParameterInfo

SHOW_DIR_REGEX = re.compile(r"^.+ \(\d{4}\) \{tvdb-\d+}\Z")

# German style patterns (case-insensitive):
#   Episode 12 Staffel 2
#   Staffel 2 Episode 12
GERMAN_EP_FIRST = re.compile(r"(?i)Episode\s+(\d+)\D+Staffel\s+(\d+)")
GERMAN_SEASON_FIRST = re.compile(r"(?i)Staffel\s+(\d+)\D+Episode\s+(\d+)")

# Common media file extensions we care about. (Lowercase, without dot.)
MEDIA_EXTS = {
    "mp4",
    "mkv",
    "avi",
    "mov",
    "m4v",
    "flv",
    "wmv",
    "mpg",
    "mpeg",
}


def _is_show_dir(path: Path) -> bool:
    return path.is_dir() and SHOW_DIR_REGEX.match(path.name) is not None


def _iter_show_dirs(root: Path):
    """Yield show directories beneath root.

    A show directory can appear directly under root or nested one (or more)
    levels deep underneath grouping folders (like 'anime sub', 'serien', etc.).
    We therefore walk the tree and emit any directory whose *name* matches the
    show pattern. We do not recurse *into* detected show folders beyond their
    immediate children; only their top level files are considered, allowing
    existing `Season NN` directories to remain untouched.
    """
    for dirpath, dirnames, _ in os.walk(root):
        parent = Path(dirpath)
        # Work on a copy to be able to prune recursion into show dirs.
        for d in list(dirnames):
            p = parent / d
            if _is_show_dir(p):
                yield p
                # Prevent os.walk from descending further inside; we handle
                # that separately.
                try:
                    dirnames.remove(d)
                except ValueError:
                    pass


def _parse_season_episode_from_name(name: str) -> tuple[int, int] | None:
    """Extract (season, episode) from filename.

    Order in target filename is season then episode per spec, and we return
    (season, episode) for internal consistency with other helpers.
    """
    # 1. Standard SxxExx pattern via existing helper
    tag = parse_episode_tag(name)
    if tag:
        season, ep1, _ = tag
        return (season, ep1)

    # 2. German 'Episode N Staffel M'
    m = GERMAN_EP_FIRST.search(name)
    if m:
        try:
            ep = int(m.group(1))
            season = int(m.group(2))
            return (season, ep)
        except ValueError:
            return None

    # 3. German 'Staffel M Episode N'
    m = GERMAN_SEASON_FIRST.search(name)
    if m:
        try:
            season = int(m.group(1))
            ep = int(m.group(2))
            return (season, ep)
        except ValueError:
            return None

    return None


def _validate_show(show_dir: Path) -> tuple[bool, list[str]]:
    """Validate a show directory.

    Checks performed:
    - presence of a TVDB id in the folder name ("{tvdb-<digits>}")
    - duplicate episode detections among loose media files (same season/episode)

    Returns (is_valid, messages). If is_valid is False the caller should skip
    performing any renames or creating season folders for this show.
    """
    msgs: list[str] = []
    name = show_dir.name

    if __import__("re").search(r"\{tvdb-\d+\}", name) is None:
        msgs.append(f"❌ ERROR: missing tvdb id in show folder name: '{name}'")

    # Collect loose media files and map parsed (season, ep) -> files
    counts: dict[tuple[int, int], list[Path]] = {}
    for entry in sorted(show_dir.iterdir()):
        if entry.is_dir() or entry.name.startswith('.'):
            continue
        ext = entry.suffix.lower().lstrip('.')
        if ext not in MEDIA_EXTS:
            continue
        parsed = _parse_season_episode_from_name(entry.name)
        if not parsed:
            msgs.append(
                f"WARN: could not parse season/episode from filename: {entry.name}")
            continue
        season, ep = parsed
        counts.setdefault((season, ep), []).append(entry)

    # Detect duplicates: same season/episode mapped by multiple files
    for (season, ep), files in counts.items():
        if len(files) > 1:
            file_list = ", ".join(str(p.name) for p in files)
            msgs.append(
                f"❌ ERROR: duplicate episode detected S{season:02d}E{ep:02d}: {file_list}")

    return (len([m for m in msgs if m.startswith("❌ ERROR:")]) == 0, msgs)


__all__ = ["PrepareUtility"]


class PrepareUtility(BaseUtility):
    """Class wrapper around the procedural process function."""

    command = "prepare"
    brief_description = "Prepare a library by moving loose episode files into Season folders and renaming them"
    result_label = "Episodes processed"
    parameters = [
        ParameterInfo(
            name="--lib",
            required=False,
            description="Path to the library to process",
            default="./data/library-p"
        ),
        ParameterInfo(
            name="--dry-run",
            required=False,
            description="Show planned moves/renames without changing the filesystem",
            default=False
        ),
    ]

    def process(self, root: Path | str | None = None) -> tuple[int]:
        """Process a root folder and normalise loose episode files using the
        instance logging helpers from BaseUtility.

        Returns
        -------
        tuple[int]
            A 1-tuple containing the total number of episode files renamed
            (sum of per-show "RENAMED" counts). Per-show statistics are
            recorded on the utility instance in `self.statistics` and a
            summary is logged via `self.log_statistics("table")`.
        """
        if root is None:
            root = Path("data/library-p")
        if not isinstance(root, Path):
            root = Path(root)

        for show_dir in _iter_show_dirs(root):
            show_title = strip_tvdb_suffix(show_dir.name)  # 'Name (YYYY)'

            # Validate show before making any changes
            valid, messages = _validate_show(show_dir)
            for m in messages:
                if m.startswith("❌ ERROR:"):
                    # strip existing prefix; BaseUtility will add its own
                    msg = m.split("❌ ERROR:", 1)[1].strip()
                    self.log_error(msg)
                elif m.startswith("WARN:"):
                    msg = m.split("WARN:", 1)[1].strip()
                    self.log_warning(msg)
                else:
                    self.log_info(m)

            if not valid:
                err_count = sum(
                    1 for m in messages if m.startswith("❌ ERROR:"))
                if err_count:
                    self.increment_stat(show_title, "ERRORS", err_count)
                self.log_warning(
                    f"SKIP show due to validation errors: {show_dir}")
                continue

            for entry in sorted(show_dir.iterdir()):
                if entry.is_dir():
                    # Skip directories (existing Season NN / other folders)
                    continue
                if entry.name.startswith('.'):
                    continue
                ext = entry.suffix.lower().lstrip('.')
                if ext not in MEDIA_EXTS:
                    continue

                parsed = _parse_season_episode_from_name(entry.name)
                if not parsed:
                    continue
                season, episode = parsed
                season_dir = show_dir / f"Season {season:02d}"
                target_name = f"{show_title} - s{season:02d}e{episode:02d}{entry.suffix.lower()}"
                target_path = season_dir / target_name

                # Skip if already correct location/name
                if entry == target_path:
                    continue

                # Ensure season directory
                if self.dry_run and not season_dir.exists():
                    self.log_info(f"MKDIR: {season_dir}")
                elif not self.dry_run:
                    season_dir.mkdir(parents=True, exist_ok=True)

                # If only case differs and same parent, use two-step rename.
                if entry.parent == target_path.parent and entry.name.lower() == target_path.name.lower():
                    ok = two_step_case_rename(
                        entry, target_path, dry_run=self.dry_run)
                    if ok:
                        # record as a successful rename for this show
                        self.increment_stat(show_title, "RENAMED")
                    else:
                        self.increment_stat(show_title, "ERRORS")
                        self.log_error(
                            f"two-step case rename failed: {entry} -> {target_path}")
                    continue

                # If destination exists (different file), skip.
                if target_path.exists() and target_path != entry:
                    self.log_warning(f"SKIP exists: {target_path}")
                    self.increment_stat(show_title, "SKIPPED")
                    continue

                if self.dry_run:
                    self.log_info(
                        f"MOVE+RENAME (dry-run): {entry} -> {target_path}")
                    self.increment_stat(show_title, "RENAMED")
                    continue

                try:
                    entry.rename(target_path)
                    self.increment_stat(show_title, "RENAMED")
                    self.log_info(f"MOVED: {entry} -> {target_path}")
                except OSError as e:
                    self.log_error(
                        f"failed to move {entry} -> {target_path}: {e}")
                    self.increment_stat(show_title, "ERRORS")

        self.log_statistics("table")

        total_errors = sum(self.statistics.get(
            s, {}).get("ERRORS", 0) for s in self.statistics.keys())
        if total_errors:
            self.log_error(
                f"{total_errors} file(s) failed during prepare; see above for details.")

        total_processed = sum(self.statistics.get(
            s, {}).get("RENAMED", 0) for s in self.statistics.keys())
        return (total_processed,)


if __name__ == "__main__":  # pragma: no cover
    import argparse
    import sys

    ap = argparse.ArgumentParser(
        description="Prepare a media library by organising loose TV episode files into season folders.")
    ap.add_argument("root", type=Path, help="Root directory to scan")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show planned operations without modifying the filesystem")
    ns = ap.parse_args()
    util = PrepareUtility(dry_run=ns.dry_run)
    count, = util.process(ns.root)
    print(f"Done. Episodes processed: {count}.")
    sys.exit(0)
