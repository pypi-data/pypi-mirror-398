def format_resolution(res: tuple[int, int] | None) -> str:
    """Format a resolution tuple as 'WxH' or 'unknown'."""
    return f"{res[0]}x{res[1]}" if res else "unknown"
