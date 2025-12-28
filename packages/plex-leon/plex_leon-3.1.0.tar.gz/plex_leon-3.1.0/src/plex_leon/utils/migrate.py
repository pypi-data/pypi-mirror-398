import os
from pathlib import Path
from typing import List
import argparse
from plex_leon.shared import (
    extract_tvdb_id,
    move_file,
    file_size,
    read_video_resolution,
    iter_nonhidden_entries,
    parse_season_episode,
    format_bytes,
    format_resolution,
)
from plex_leon.utils.base_utility import BaseUtility, ParameterInfo


class MigrateUtility(BaseUtility):
    """Class wrapper around the migration logic moved here so instance
    logging helpers can be used (log_info/log_warning/log_error).

    Usage:
        MigrateUtility(dry_run=True).process(lib_a, lib_b, lib_c, overwrite=False)
    """

    command = "migrate"
    brief_description = "Move items from library-a to library-c when their TVDB ID exists in library-b."
    result_label = "Eligible files/folders moved"
    requires_tools_check = True
    parameters = [
        ParameterInfo(
            name="--lib-a",
            required=False,
            description="Path to library-a",
            default="./data/library-a"
        ),
        ParameterInfo(
            name="--lib-b",
            required=False,
            description="Path to library-b",
            default="./data/library-b"
        ),
        ParameterInfo(
            name="--lib-c",
            required=False,
            description="Path to library-c",
            default="./data/library-c"
        ),
        ParameterInfo(
            name="--overwrite",
            required=False,
            description="Overwrite existing files in library-c",
            default=False
        ),
        ParameterInfo(
            name="--dry-run",
            required=False,
            description="Show what would be moved, but do not actually move files",
            default=False
        ),
        ParameterInfo(
            name="--threads",
            required=False,
            description="Optional thread count for metadata reads (I/O bound)",
            default=None
        ),
        ParameterInfo(
            name="--no-resolution",
            required=False,
            description="Skip resolution comparisons to speed up large runs",
            default=False
        ),
    ]

    @classmethod
    def prepare_process_args(cls, args: argparse.Namespace) -> tuple[tuple, dict]:
        """Convert argparse args to process() parameters."""
        # Extract positional arguments
        positional = (args.lib_a, args.lib_b, args.lib_c)

        # Build kwargs with the remaining parameters
        kwargs = {
            'overwrite': args.overwrite,
            'dry_run': args.dry_run,
            'threads': args.threads,
            'prefer_resolution': not args.no_resolution,
        }

        return positional, kwargs

    def process(self, lib_a: Path, lib_b: Path, lib_c: Path, **kwargs) -> tuple[int, int]:
        # accept overwrite/dry_run/prefer_resolution/threads forwarded via kwargs
        overwrite: bool = kwargs.get("overwrite", False)
        dry_run: bool = kwargs.get("dry_run", self.dry_run)
        prefer_resolution: bool = kwargs.get("prefer_resolution", True)
        threads: int | None = kwargs.get("threads", None)

        if not lib_a.is_dir():
            self.log_error(f"library-a not found: {lib_a}")
            return (0, 0)
        if not lib_b.is_dir():
            self.log_error(f"library-b not found: {lib_b}")
            return (0, 0)

        b_ids: set[str] = set()
        b_index: dict[str, list[Path]] = {}
        # Recursively collect TVDB ids from library-b to support bucketed layout (A-Z, 0-9)
        for b_entry in iter_nonhidden_entries(lib_b):
            b_tvdb = extract_tvdb_id(b_entry.name)
            if not b_tvdb:
                continue
            b_ids.add(b_tvdb)
            b_index.setdefault(b_tvdb, []).append(b_entry)

        self.log_info(f"🔎 Found {len(b_ids)} tvdb-ids in library-b")

        # Helper lambdas for concise logging
        _fmt_res = format_resolution
        _fmt_size = format_bytes

        # Lazy cache: per-TVDB episode index for library-b shows
        # tvdb -> {(season, ep): Path}
        b_episode_index_cache: dict[str, dict[tuple[int, int], Path]] = {}

        # Resolution cache to avoid repeated probes
        from functools import lru_cache

        @lru_cache(maxsize=4096)
        def _res_cached(p: str) -> tuple[int, int] | None:
            return read_video_resolution(Path(p))

        def _get_res(path: Path) -> tuple[int, int] | None:
            return _res_cached(path.as_posix())

        def _build_episode_index(show_dirs: list[Path]) -> dict[tuple[int, int], Path]:
            idx: dict[tuple[int, int], Path] = {}
            for d in show_dirs:
                if not d.is_dir():
                    continue
                for dirpath, _, filenames in os.walk(d):
                    for fn in filenames:
                        if fn.startswith('.'):
                            continue
                        se = parse_season_episode(fn)
                        if not se:
                            # Try double-episode parsing to index both
                            from ..shared import parse_episode_tag
                            parsed = parse_episode_tag(fn)
                            if not parsed:
                                continue
                            s, e1, e2 = parsed
                            idx.setdefault((s, e1), Path(dirpath) / fn)
                            if e2 is not None:
                                idx.setdefault((s, e2), Path(dirpath) / fn)
                            continue
                        s, e = se
                        idx.setdefault((s, e), Path(dirpath) / fn)
            return idx

        # Optional thread pool for prefetching resolutions (I/O bound)
        executor = None
        if threads and threads > 1 and prefer_resolution:
            from concurrent.futures import ThreadPoolExecutor
            executor = ThreadPoolExecutor(max_workers=threads)

        for entry in lib_a.iterdir():
            if entry.name.startswith('.'):
                continue
            tvdb = extract_tvdb_id(entry.name)
            if not tvdb:
                self.increment_stat(entry.name, "SKIPPED")
                continue
            if tvdb in b_ids:
                # Movies are files; TV shows are folders. Apply per-episode logic for TV shows.
                if entry.is_file():
                    # Find a counterpart in lib_b with the same tvdb id that is a file (movie)
                    candidates = [p for p in b_index.get(
                        tvdb, []) if p.is_file()]
                    b_match: Path | None = candidates[0] if candidates else None

                    # Compare resolution if both can be read
                    better_resolution = False
                    # Only probe resolution if both sides exist; otherwise skip expensive metadata.
                    if prefer_resolution and b_match is not None:
                        res_a = _get_res(entry)
                        res_b = _get_res(b_match)
                    else:
                        res_a = None
                        res_b = None
                    if res_a and res_b:
                        pixels_a = res_a[0] * res_a[1]
                        pixels_b = res_b[0] * res_b[1]
                        better_resolution = pixels_a > pixels_b

                    # Always compute sizes for details in logs
                    size_a = file_size(entry)
                    size_b = file_size(b_match) if b_match is not None else 0

                    # Decide destination and reason
                    if better_resolution:
                        dest_base = lib_c / "better-resolution"
                        reason = "better-resolution"
                    else:
                        # Fall back to file size comparison
                        if size_a > size_b:
                            dest_base = lib_c / "greater-filesize"
                            reason = "greater-filesize"
                        else:
                            dest_base = lib_c / "to-delete"
                            reason = "to-delete"

                    # Pretty formatting helpers
                    # Log the decision with details
                    b_name = b_match.name if b_match is not None else "<missing>"
                    self.log_info(
                        f"🔁 DECISION: {entry.name} -> {dest_base.name} reason={reason} "
                        f"A[res={_fmt_res(res_a)}, size={_fmt_size(size_a)}] "
                        f"B(name={b_name})[res={_fmt_res(res_b)}, size={_fmt_size(size_b)}]"
                    )

                    dest = dest_base / entry.name
                    move_file(entry, dest, overwrite=overwrite,
                              dry_run=dry_run)
                    key = tvdb or entry.name
                    self.increment_stat(key, "MOVED")
                else:
                    # For folders (TV shows), compare and move episodes individually
                    show_dirs_in_b = [
                        p for p in b_index.get(tvdb, []) if p.is_dir()]
                    # Build or reuse episode index for this TVDB id
                    if tvdb not in b_episode_index_cache:
                        b_episode_index_cache[tvdb] = _build_episode_index(
                            show_dirs_in_b)
                    ep_idx = b_episode_index_cache[tvdb]
                    # Walk seasons and episodes under this show
                    for dirpath, _, filenames in os.walk(entry):
                        for fn in filenames:
                            if fn.startswith('.'):
                                continue
                            src_ep = Path(dirpath) / fn
                            # Parse season/episode; skip non-matching files
                            se = parse_season_episode(fn)
                            if not se:
                                self.increment_stat(tvdb, "SKIPPED")
                                continue
                            season_num, ep_num = se
                            b_ep = ep_idx.get((season_num, ep_num))

                            # Compare resolution when possible
                            better_resolution = False
                            if prefer_resolution and b_ep is not None:
                                # Optional prefetch of resolutions in a thread pool
                                if executor is not None:
                                    # Kick off async reads to warm cache
                                    executor.submit(_get_res, src_ep)
                                    executor.submit(_get_res, b_ep)
                                res_a = _get_res(src_ep)
                                res_b = _get_res(b_ep)
                            else:
                                res_a = None
                                res_b = None
                            if res_a and res_b:
                                pixels_a = res_a[0] * res_a[1]
                                pixels_b = res_b[0] * res_b[1]
                                better_resolution = pixels_a > pixels_b

                            size_a = file_size(src_ep)
                            size_b = file_size(b_ep) if b_ep is not None else 0

                            if better_resolution:
                                dest_base = lib_c / "better-resolution"
                                reason = "better-resolution"
                            else:
                                if size_a > size_b:
                                    dest_base = lib_c / "greater-filesize"
                                    reason = "greater-filesize"
                                else:
                                    dest_base = lib_c / "to-delete"
                                    reason = "to-delete"

                            # Pretty formatting helpers (reuse local lambdas)
                            b_name = b_ep.name if b_ep is not None else "<missing>"
                            self.log_info(
                                f"🔁 DECISION: {src_ep.name} -> {dest_base.name} reason={reason} "
                                f"A[res={_fmt_res(res_a)}, size={_fmt_size(size_a)}] "
                                f"B(name={b_name})[res={_fmt_res(res_b)}, size={_fmt_size(size_b)}]"
                            )

                            # Preserve show/season structure under destination
                            try:
                                rel_path = src_ep.relative_to(entry)
                            except ValueError:
                                rel_path = Path(src_ep.name)
                            dest = dest_base / entry.name / rel_path
                            move_file(src_ep, dest, overwrite=overwrite,
                                      dry_run=dry_run)
                            key = tvdb or entry.name
                            self.increment_stat(key, "MOVED")
                    # Do not move the show folder itself
            else:
                # track skipped by folder name
                key = extract_tvdb_id(entry.name) or entry.name
                self.increment_stat(key, "SKIPPED")

        # Clean up thread pool if created
        if executor is not None:
            executor.shutdown(wait=True)

        # Print per-show summaries via BaseUtility statistics helper
        self.log_statistics("table")

        total_errors = sum(
            stats.get("ERRORS", 0) for stats in self.statistics.values()
        )
        if total_errors:
            self.log_error(
                f"{total_errors} item(s) failed during migrate; see above for details.")

        total_moved = sum(
            stats.get("MOVED", 0) for stats in self.statistics.values()
        )
        total_skipped = sum(
            stats.get("SKIPPED", 0) for stats in self.statistics.values()
        )

        return total_moved, total_skipped
