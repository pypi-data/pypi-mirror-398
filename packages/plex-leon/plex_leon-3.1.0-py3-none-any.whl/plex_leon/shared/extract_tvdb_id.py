
from plex_leon.shared import TVDB_REGEX


def extract_tvdb_id(name: str) -> str | None:
    """Return the TVDB id embedded in a filename/folder name or None.

    Example: "John Wick (2014) {tvdb-155}.mp4" -> "155"
    """
    media = TVDB_REGEX.search(name)
    return media.group(1) if media else None
