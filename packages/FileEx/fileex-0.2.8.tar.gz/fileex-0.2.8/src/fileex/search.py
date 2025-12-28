from pathlib import Path as _Path

from fileex import exception as _exception


def path_in_hierarchy(
    path: str | _Path,
    leaf_dir: str | _Path = ".",
    root_dir: str | _Path = "/",
) -> _Path | None:
    """Find a path in the directory hierarchy.

    Parameters
    ----------
    path : str | pathlib.Path
        Relative path to the file or directory to find.
    leaf_dir : str | pathlib.Path, default: "."
        Directory to start the search from.
    root_dir : str | pathlib.Path, default: "/"
        Directory to stop the search at.
        This must be an ancestor of `leaf_dir`.

    Returns
    -------
    path : pathlib.Path | None
        Absolute path to the file or directory if found, else None.
    """
    path = _Path(path)
    leaf_dir = _Path(leaf_dir).resolve()
    root_dir = _Path(root_dir).resolve()
    try:
        leaf_dir.relative_to(root_dir)
    except ValueError:
        raise _exception.FileExInputError("Input argument 'leaf_dir' must be a descendant of 'root_dir'.")
    while leaf_dir != root_dir:
        possible_path = leaf_dir / path
        if possible_path.exists():
            return possible_path
        leaf_dir = leaf_dir.parent
    return
