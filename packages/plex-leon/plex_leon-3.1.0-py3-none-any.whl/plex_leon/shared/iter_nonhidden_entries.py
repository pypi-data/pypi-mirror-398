import os
from pathlib import Path


def iter_nonhidden_entries(root: Path):
    """Yield non-hidden files and directories recursively under root.

    Hidden directories and files (starting with '.') are skipped.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for d in dirnames:
            yield Path(dirpath) / d
        for f in filenames:
            if f.startswith('.'):
                continue
            yield Path(dirpath) / f
