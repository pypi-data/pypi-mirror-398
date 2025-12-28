from pathlib import Path


def unique_swap_path(parent: Path, base_name: str) -> Path:
    """Return a unique temporary swap path '.plexleon_swap_<base_name>[.n]'."""
    swap_path = parent / f".plexleon_swap_{base_name}"
    i = 1
    while swap_path.exists():
        swap_path = parent / f".plexleon_swap_{base_name}.{i}"
        i += 1
    return swap_path
