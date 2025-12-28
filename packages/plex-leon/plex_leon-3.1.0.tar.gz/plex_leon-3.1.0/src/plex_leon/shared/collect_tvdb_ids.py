
from pathlib import Path
from plex_leon.shared import extract_tvdb_id


def collect_tvdb_ids(path: Path) -> set[str]:
    """Collect TVDB ids from the immediate children of a directory.

    Hidden entries (starting with a dot) are ignored. Both files and folders
    are considered.
    """
    ids: set[str] = set()
    for entry in path.iterdir():
        if not entry.name.startswith("."):
            tvdb = extract_tvdb_id(entry.name)
            if tvdb:
                ids.add(tvdb)
    return ids
