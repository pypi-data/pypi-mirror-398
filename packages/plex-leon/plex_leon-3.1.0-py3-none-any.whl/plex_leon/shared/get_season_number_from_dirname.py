from plex_leon.shared import _SEASON_DIGITS_RE


def get_season_number_from_dirname(name: str) -> int | None:
    """Extract the single season number from a folder name if unambiguous.

    Returns the integer season number when the name contains exactly one
    contiguous sequence of digits; otherwise returns None.
    """
    digits = _SEASON_DIGITS_RE.findall(name)
    if len(digits) != 1:
        return None
    try:
        num = int(digits[0])
        if num < 0:
            return None
        return num
    except ValueError:
        return None
