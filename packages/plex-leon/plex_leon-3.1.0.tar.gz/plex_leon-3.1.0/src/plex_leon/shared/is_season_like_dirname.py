
from plex_leon.shared import _SEASON_DIGITS_RE


def is_season_like_dirname(name: str) -> bool:
    """Heuristic to detect season directory names: contains exactly one number chunk."""
    return len(_SEASON_DIGITS_RE.findall(name)) == 1
