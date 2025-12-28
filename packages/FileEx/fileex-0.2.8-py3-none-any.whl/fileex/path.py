from pathlib import Path
from typing import Any


def is_path(path: Any) -> bool:
    """Check if the input is a path.

    The input is considered a path if it is a `pathlib.Path` object
    or a string representing a path that exists on the filesystem.

    Parameters
    ----------
    path
        Path to check.
    """
    if isinstance(path, Path):
        return True
    if not isinstance(path, str):
        return False
    try:
        return Path(path).exists()
    except OSError:
        # If the path cannot be resolved, it is not a valid path (e.g., too long)
        return False
