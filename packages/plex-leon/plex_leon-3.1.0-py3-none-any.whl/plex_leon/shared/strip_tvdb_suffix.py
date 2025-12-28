
from plex_leon.shared import TVDB_SUFFIX_REGEX


def strip_tvdb_suffix(name: str) -> str:
    """Remove occurrences of ' {tvdb-...}' from a name and trim whitespace.

    Example: 'Code Geass (2006) {tvdb-79525}' -> 'Code Geass (2006)'
    """
    return TVDB_SUFFIX_REGEX.sub("", name).strip()