
from pathlib import Path
import shutil


def move_file(src: Path, dst: Path, *, overwrite: bool, dry_run: bool) -> None:
    """Move a file/folder from src to dst.

    - Creates destination parent directories as needed.
    - Prints an action message (or a skip message when not overwriting).
    - If dry_run=True, only prints without modifying the filesystem.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not overwrite:
        print(f"⚠️  SKIP exists: {dst}")
        return
    print(f"📦 MOVE: {src} -> {dst}")
    if dry_run:
        return
    if dst.exists():
        if dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    shutil.move(src.as_posix(), dst.as_posix())