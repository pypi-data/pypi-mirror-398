
import os
from pathlib import Path


def find_episode_in_dirs(show_dirs: list[Path], season: int, episode: int) -> Path | None:
    """Search for an episode file within provided show directories.

    Matches case-insensitively on the substring 'sNNeMM' in filenames.
    """
    needle_upper = f"s{season:02d}e{episode:02d}".upper()
    for d in show_dirs:
        if not d.is_dir():
            continue
        for dirpath, _, filenames in os.walk(d):
            for fn in filenames:
                if fn.startswith('.'):
                    continue
                if needle_upper in fn.upper():
                    return Path(dirpath) / fn
    return None
