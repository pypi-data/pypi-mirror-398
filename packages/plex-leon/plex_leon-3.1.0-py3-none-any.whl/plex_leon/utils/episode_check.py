"""Episode check utility for comparing local episodes with TVDB data.

This module provides an `EpisodeCheckUtility` that scans a library directory
for TV show folders and compares the number of episodes per season with the
episode counts from TVDB.

The utility:
1. Scans for show folders matching the pattern: TV Show Name (YYYY) {tvdb-12345}
2. Counts episodes in each Season NN folder
3. Fetches episode counts from TVDB API
4. Displays a comparison table showing any discrepancies

Requires TVDB_API_KEY environment variable to be set.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from plex_leon.api import TVDBClient
from plex_leon.shared import strip_tvdb_suffix
from plex_leon.utils.base_utility import BaseUtility, ParameterInfo

SHOW_DIR_REGEX = re.compile(r"^.+ \(\d{4}\) \{tvdb-(\d+)\}\Z")
SEASON_DIR_REGEX = re.compile(r"^Season (\d+)\Z", re.IGNORECASE)

# Common media file extensions
MEDIA_EXTS = {
    "mp4", "mkv", "avi", "mov", "m4v", "flv", "wmv", "mpg", "mpeg",
}


def _extract_tvdb_id(dirname: str) -> Optional[int]:
    """Extract TVDB ID from show directory name.
    
    Parameters
    ----------
    dirname : str
        Directory name like "Show Name (2024) {tvdb-12345}"
    
    Returns
    -------
    int or None
        TVDB ID if found, None otherwise.
    """
    match = SHOW_DIR_REGEX.match(dirname)
    if match:
        return int(match.group(1))
    return None


def _is_media_file(path: Path) -> bool:
    """Check if a file is a media file based on extension."""
    if not path.is_file():
        return False
    ext = path.suffix.lower().lstrip('.')
    return ext in MEDIA_EXTS


def _count_episodes_in_season(season_dir: Path) -> int:
    """Count media files in a season directory."""
    if not season_dir.is_dir():
        return 0
    return sum(1 for f in season_dir.iterdir() if _is_media_file(f))


def _get_local_episode_counts(show_dir: Path) -> Dict[int, int]:
    """Get episode counts per season from local filesystem.
    
    Parameters
    ----------
    show_dir : Path
        Path to the show directory.
    
    Returns
    -------
    Dict[int, int]
        Mapping of season number to episode count.
    """
    season_counts: Dict[int, int] = {}
    
    for entry in show_dir.iterdir():
        if not entry.is_dir():
            continue
        
        match = SEASON_DIR_REGEX.match(entry.name)
        if match:
            season_num = int(match.group(1))
            # Skip specials (season 0)
            if season_num == 0:
                continue
            count = _count_episodes_in_season(entry)
            if count > 0:
                season_counts[season_num] = count
    
    return season_counts


def _iter_show_dirs(root: Path):
    """Yield show directories with TVDB IDs beneath root.
    
    Walks the directory tree and yields any directory whose name matches
    the show pattern with a TVDB ID.
    """
    for dirpath, dirnames, _ in os.walk(root):
        parent = Path(dirpath)
        for d in list(dirnames):
            p = parent / d
            if _extract_tvdb_id(p.name):
                yield p
                # Don't recurse into show directories
                try:
                    dirnames.remove(d)
                except ValueError:
                    pass


__all__ = ["EpisodeCheckUtility"]


class EpisodeCheckUtility(BaseUtility):
    """Utility for checking episode counts against TVDB."""
    
    command = "episode-check"
    brief_description = "Compare local episode counts with TVDB data"
    result_label = "Shows checked"
    parameters = [
        ParameterInfo(
            name="--lib",
            required=False,
            description="Path to the library to check",
            default="./data/library-p"
        ),
    ]
    
    def __init__(self, dry_run: bool = False):
        """Initialize the utility.
        
        Parameters
        ----------
        dry_run : bool
            Currently unused for this utility (no filesystem modifications).
        """
        super().__init__(dry_run=dry_run)
        self._tvdb_client: Optional[TVDBClient] = None
    
    @property
    def tvdb_client(self) -> TVDBClient:
        """Lazy-load TVDB client."""
        if self._tvdb_client is None:
            try:
                self._tvdb_client = TVDBClient()
            except (ValueError, ImportError) as e:
                self.log_error(f"Failed to initialize TVDB client: {e}")
                raise
        return self._tvdb_client
    
    def _format_comparison_table(
        self,
        show_name: str,
        local_counts: Dict[int, int],
        tvdb_counts: Dict[int, int]
    ) -> str:
        """Format a comparison table for a show.
        
        Parameters
        ----------
        show_name : str
            Name of the show.
        local_counts : Dict[int, int]
            Local episode counts per season.
        tvdb_counts : Dict[int, int]
            TVDB episode counts per season.
        
        Returns
        -------
        str
            Formatted table string.
        """
        # Get all season numbers
        all_seasons = sorted(set(local_counts.keys()) | set(tvdb_counts.keys()))
        
        if not all_seasons:
            return f"\n{show_name}: No seasons found"
        
        lines = [f"\n{show_name}:"]
        lines.append("  Season | Downloaded | TVDB")
        lines.append("  -------|------------|-----")
        
        has_diff = False
        for season in all_seasons:
            local = local_counts.get(season, 0)
            tvdb = tvdb_counts.get(season, 0)
            
            if local != tvdb:
                has_diff = True
                lines.append(f"  {season:6} | {local:10} | {tvdb:4} ⚠️")
            else:
                lines.append(f"  {season:6} | {local:10} | {tvdb:4}")
        
        if not has_diff:
            return ""  # Don't show if everything matches
        
        return "\n".join(lines)
    
    def process(self, root: Path | str | None = None) -> tuple[int]:
        """Process a library and check episode counts against TVDB.
        
        Parameters
        ----------
        root : Path or str, optional
            Root directory to scan. Defaults to "./data/library-p".
        
        Returns
        -------
        tuple[int]
            A 1-tuple containing the number of shows checked.
        """
        if root is None:
            root = Path("data/library-p")
        if not isinstance(root, Path):
            root = Path(root)
        
        if not root.exists():
            self.log_error(f"Library path does not exist: {root}")
            return (0,)
        
        # Check for TVDB API key
        if not os.environ.get("TVDB_API_KEY"):
            self.log_error(
                "TVDB_API_KEY environment variable is not set. "
                "Please set it to use this utility."
            )
            return (0,)
        
        shows_checked = 0
        shows_with_diffs = 0
        
        for show_dir in _iter_show_dirs(root):
            tvdb_id = _extract_tvdb_id(show_dir.name)
            if not tvdb_id:
                continue
            
            show_title = strip_tvdb_suffix(show_dir.name)
            
            # Get local episode counts
            local_counts = _get_local_episode_counts(show_dir)
            
            if not local_counts:
                self.log_info(f"SKIP (no episodes): {show_title}")
                continue
            
            # Get TVDB episode counts
            try:
                tvdb_counts = self.tvdb_client.get_series_episodes(tvdb_id)
            except Exception as e:
                self.log_error(f"Failed to fetch TVDB data for {show_title}: {e}")
                self.increment_stat(show_title, "ERRORS")
                continue
            
            shows_checked += 1
            
            # Compare and display results
            table = self._format_comparison_table(show_title, local_counts, tvdb_counts)
            if table:
                print(table)
                shows_with_diffs += 1
                self.increment_stat(show_title, "HAS_DIFF")
            else:
                self.increment_stat(show_title, "OK")
        
        # Summary
        if shows_checked > 0:
            print(f"\n{'='*60}")
            print(f"Summary: {shows_checked} show(s) checked")
            if shows_with_diffs > 0:
                print(f"  ⚠️  {shows_with_diffs} show(s) have episode count differences")
            else:
                print("  ✓ All shows match TVDB episode counts")
            print(f"{'='*60}")
        else:
            self.log_warning("No shows found to check")
        
        return (shows_checked,)


if __name__ == "__main__":  # pragma: no cover
    import argparse
    import sys
    
    ap = argparse.ArgumentParser(
        description="Check episode counts against TVDB data.")
    ap.add_argument("root", type=Path, help="Root directory to scan")
    ns = ap.parse_args()
    
    util = EpisodeCheckUtility()
    count, = util.process(ns.root)
    sys.exit(0)
