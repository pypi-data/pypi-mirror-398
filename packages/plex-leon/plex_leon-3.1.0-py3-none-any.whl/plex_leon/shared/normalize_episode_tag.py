
from plex_leon.shared import EPISODE_TAG_REGEX, parse_episode_tag


def normalize_episode_tag(text: str) -> str | None:
    """Return the normalized lowercase episode tag (e.g., 's01e01[-e02]') or None."""
    parsed = parse_episode_tag(text)
    if not parsed:
        return None
    s, e1, e2 = parsed
    if e2 is not None:
        return f"s{s:02d}e{e1:02d}-e{e2:02d}"
    return f"s{s:02d}e{e1:02d}"
