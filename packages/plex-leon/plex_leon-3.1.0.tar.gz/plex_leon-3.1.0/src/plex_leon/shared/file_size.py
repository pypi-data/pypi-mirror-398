
from pathlib import Path


def file_size(path: Path) -> int:
    """Return the size of a file in bytes.

    - If the path doesn't exist or isn't a regular file, returns 0.
    - Never raises for missing files; use path.exists() if you need strict checks.
    """
    try:
        return path.stat().st_size if path.is_file() else 0
    except FileNotFoundError:
        return 0
