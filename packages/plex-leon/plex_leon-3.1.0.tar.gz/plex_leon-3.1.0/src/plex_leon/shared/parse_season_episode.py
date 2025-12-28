from plex_leon.shared import parse_episode_tag


def parse_season_episode(text: str) -> tuple[int, int] | None:
    """Return (season, episode) from text or None.

    For double-episode tags, returns the first episode number.
    """
    parsed = parse_episode_tag(text)
    if not parsed:
        return None
    s, e1, _ = parsed
    return (s, e1)