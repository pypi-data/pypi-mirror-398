
import shutil


def assert_required_tools_installed() -> None:
    """Ensure required external tools are available on PATH.

    Currently required:
    - ffprobe (from FFmpeg)
    - mediainfo

    Raises RuntimeError with a clear message if any are missing.
    """
    required = ["ffprobe", "mediainfo"]
    missing = [tool for tool in required if shutil.which(tool) is None]
    if missing:
        msg = (
            "Missing required tools: "
            + ", ".join(missing)
            + ". Please install FFmpeg (provides ffprobe) and mediainfo, then retry."
        )
        raise RuntimeError(msg)
