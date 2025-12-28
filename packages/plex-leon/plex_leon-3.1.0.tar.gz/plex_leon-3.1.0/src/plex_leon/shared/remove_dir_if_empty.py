
from pathlib import Path


def remove_dir_if_empty(path: Path) -> bool:
    """Remove directory if empty, returning True when removed."""
    try:
        next(path.iterdir())
        return False
    except StopIteration:
        try:
            path.rmdir()
            return True
        except OSError:
            return False
