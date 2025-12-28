from pathlib import Path


def merge_directory_contents(src: Path, dst: Path, conflicts_dirname: str = ".plexleon_conflicts") -> None:
    """Move all items from src into dst; existing names go under a conflicts folder.

    Creates 'dst/<conflicts_dirname>' for conflicts and ensures no overwrites by
    adding '(conflict)' or '(conflict N)' to the basename as needed.
    """
    dst.mkdir(parents=True, exist_ok=True)
    conflicts_dir = dst / conflicts_dirname
    for item in sorted(src.iterdir()):
        dest = dst / item.name
        if dest.exists():
            try:
                conflicts_dir.mkdir(exist_ok=True)
            except OSError:
                pass
            base = item.stem
            suffix = item.suffix
            n = 1
            conflict_name = f"{base} (conflict){suffix}"
            conflict_dest = conflicts_dir / conflict_name
            while conflict_dest.exists():
                conflict_name = f"{base} (conflict {n}){suffix}"
                conflict_dest = conflicts_dir / conflict_name
                n += 1
            try:
                item.rename(conflict_dest)
                print(f"⚠️  CONFLICT: moved to {conflict_dest}")
            except OSError as e:
                print(
                    f"❌ ERROR: conflict move failed {item} -> {conflict_dest}: {e}")
        else:
            try:
                item.rename(dest)
            except OSError as e:
                print(f"❌ ERROR: move failed {item} -> {dest}: {e}")
