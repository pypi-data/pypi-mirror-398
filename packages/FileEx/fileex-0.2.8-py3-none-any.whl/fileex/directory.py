from pathlib import Path
import shutil
import os
from contextlib import contextmanager
import tempfile
from typing import Iterator

from fileex import exception

__all__ = ["delete_contents"]


def delete(
    path: str | Path,
    exclude: list[str] | None = None,
    raise_existence: bool = True
) -> tuple[list[Path], list[Path]] | tuple[None, None]:
    """Recursively delete files and directories within a given directory, excluding those specified by `exclude`.

    Parameters
    ----------
    path
        Path to the directory whose content should be deleted.
    exclude
        List of glob patterns to exclude from deletion.
        Patterns are relative to the directory specified by `path`.
        If a directory is excluded, all its contents will also be excluded.
    raise_existence : bool, default: True
        Raise an error when the directory does not exist.

    Returns
    -------
        Paths of the files and directories that were deleted and excluded, respectively,
        or None if the directory does not exist and `raise_existence` is set to False.

    Raises
    ------
    fileex.exception.FileExPathNotFoundError
        If the directory does not exist and `raise_existence` is set to True.
    """
    path = Path(path).resolve()
    if not path.is_dir():
        if raise_existence:
            raise exception.FileExPathNotFoundError(path, is_dir=True)
        return None, None

    excluded_paths = set()
    for pattern in exclude or []:
        for excluded_path in path.glob(pattern):
            excluded_paths.add(excluded_path)
            if excluded_path.is_dir():
                # Also exclude all contents of the directory
                excluded_paths.update(excluded_path.rglob("*"))

    deleted = []
    # Walk bottom-up so we can delete files before trying to delete directories
    for current_dir, dirs, files in os.walk(path, topdown=False):
        current_path = Path(current_dir)
        # Delete files
        for name in files:
            file_path = current_path / name
            if file_path.resolve() in excluded_paths:
                continue
            file_path.unlink()
            deleted.append(file_path)
        # Delete directories
        for name in dirs:
            dir_path = current_path / name
            if dir_path.resolve() in excluded_paths:
                continue
            shutil.rmtree(dir_path)
            deleted.append(dir_path)
    return deleted, list(excluded_paths)


def merge(
    source: str | Path,
    destination: str | Path,
    raise_existence: bool = True
) -> list[Path] | None:
    """Recursively merge a directory into another.

    All files and subdirectories in `source` will be moved to `destination`.
    Existing files in `destination` will be overwritten.

    Parameters
    ----------
    source
        Path to the source directory.
    destination
        Path to the destination directory.
    raise_existence
        Raise an error if the source directory does not exist.

    Returns
    -------
        Paths of the files and directories that were moved,
        or None if the source directory does not exist and `raise_existence` is set to False.

    Raises
    ------
    fileex.exception.FileExPathNotFoundError
        If the source directory does not exist and `raise_existence` is set to True.
    """
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    moved_paths = []
    if not source.is_dir():
        if raise_existence:
            raise exception.FileExPathNotFoundError(source, is_dir=True)
        return None, None
    for item in source.iterdir():
        dest_item = destination / item.name
        if item.is_dir():
            if dest_item.exists():
                # Merge the subdirectory
                move_and_merge(item, dest_item)
            else:
                # Move the whole directory
                shutil.move(str(item), str(dest_item))
                moved_paths.append(dest_item)
        else:
            # Move or overwrite the file
            if dest_item.exists():
                # Remove the existing file
                dest_item.unlink()
            shutil.move(str(item), str(dest_item))
            moved_paths.append(dest_item)
    source.rmdir()
    return moved_paths


@contextmanager
def get_or_make(
    path: str | Path | None = None,
    ensure_empty: bool = False,
    suffix: str | None = None,
    prefix: str | None = None,
    dir: str | Path | None = None,
    ignore_cleanup_errors: bool = False,
    delete: bool = True
) -> Iterator[Path]:
    """Provide a directory for I/O operations.

    This context manager yields a `pathlib.Path` object
    pointing to an existing directory:
    - If `path` is provided, ensures the directory exists
      (creating it if necessary) and yields it.
    - If `path` is None, creates a temporary directory,
      yields it, and optionally removes it on exit.

    Parameters
    ----------
    path
        Filesystem path to use. If None, a temporary directory is created.
    ensure_empty
        If True, ensures that the directory is empty before yielding,
        raising an error if it is not.
    suffix
        Suffix for the temporary directory, if created.
    prefix
        Prefix for the temporary directory, if created.
    dir
        Directory in which to create the temporary directory, if created.
    ignore_cleanup_errors
        If True, ignore errors during cleanup of the temporary directory.
    delete
        If True, the temporary directory will be deleted on exit.

    Yields
    ------
    work_dir
        The directory to perform file operations in.

    Examples
    --------
    >>> with get_or_make('/tmp/data') as work_dir:
    ...     (work_dir / 'file.txt').write_text('hello')
    >>> with get_or_make() as work_dir:
    ...     # work_dir is a fresh temp dir, auto-cleaned
    ...     (work_dir / 'temp.txt').write_text('world')
    """
    if path:
        outdir = Path(path).resolve()
        if outdir.exists():
            if not outdir.is_dir():
                raise ValueError(
                    f"The specified output path '{outdir}' is not a directory."
                )
            if ensure_empty and any(outdir.iterdir()):
                raise ValueError(
                    f"The specified output directory '{outdir}' is not empty."
                )
        else:
            outdir.mkdir(parents=True, exist_ok=True)
        yield outdir
    else:
        with tempfile.TemporaryDirectory(
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            ignore_cleanup_errors=ignore_cleanup_errors,
            delete=delete,
        ) as tmpdir:
            yield Path(tmpdir)
    return
