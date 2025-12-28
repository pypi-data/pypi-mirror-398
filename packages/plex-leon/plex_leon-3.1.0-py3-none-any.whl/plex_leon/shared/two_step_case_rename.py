
from pathlib import Path


def two_step_case_rename(old_path: Path, new_path: Path, *, dry_run: bool) -> bool:
    """Perform a two-step rename to handle case-only changes reliably.

    Returns True on success, False otherwise. Prints actions. Does not merge directories.
    """
    parent = old_path.parent
    swap_name = f".plexleon_swap_{new_path.name}"
    swap_path = parent / swap_name
    i = 1
    while swap_path.exists():
        swap_path = parent / f"{swap_name}.{i}"
        i += 1

    if dry_run:
        print(f"🔁 RENAME: {old_path} -> {swap_path}")
        print(f"🔁 RENAME: {swap_path} -> {new_path}")
        return True

    try:
        old_path.rename(swap_path)
        if new_path.exists():
            print(f"⚠️  SKIP exists: {new_path}")
            try:
                swap_path.rename(old_path)
            except OSError:
                pass
            return False
        swap_path.rename(new_path)
        return True
    except OSError as e:
        print(f"❌ ERROR: two-step rename failed {old_path} -> {new_path}: {e}")
        try:
            if swap_path.exists():
                swap_path.rename(old_path)
        except OSError:
            pass
        return False
