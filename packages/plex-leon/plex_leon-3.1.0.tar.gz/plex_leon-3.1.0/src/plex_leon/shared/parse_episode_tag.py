from plex_leon.shared import EPISODE_TAG_REGEX


def parse_episode_tag(text: str) -> tuple[int, int, int | None] | None:
    """Parse an episode tag from text and return (season, ep1, ep2_or_None).

    Supports 's01e01', 'S01E01', and double episodes like 'S01E01-E02'.
    Returns None when no tag is found or parsing fails.
    """
    m = EPISODE_TAG_REGEX.search(text)
    if not m:
        return None
    try:
        s = int(m.group(1))
        e1 = int(m.group(2))
        e2s = m.group(3)
        e2 = int(e2s) if e2s is not None else None
        return (s, e1, e2)
    except ValueError:
        return None
