from pathlib import Path
from typing import IO, Literal, overload
import io
import os

import fileex
from fileex.typing import FileLike, ReadableFileLike


def open_file(
    source: str | bytes | Path,
    mode: str = 'r',
    encoding: str | None = None
) -> IO[str] | IO[bytes]:
    """Create an open file-like object from content or filepath.

    If `source` is a `str` or `bytes`, returns an in-memory
    file-like object containing that content. If `source` is a
    `pathlib.Path`, opens the file at that path with the
    specified mode.

    Parameters
    ----------
    source
        File content (as string or bytes)
        or path (as string or pathlib.Path).
        If a string is provided, it is first checked
        if it is a valid existing file path.
        If so, the string is treated as a path,
        otherwise as file content.
        Bytes are always treated as content,
        and a `pathlib.Path` is always treated as a file path.
    mode
        Mode (e.g., 'r', 'w', 'rb') to open the file when `source` is a path.
        Ignored when `source` is content.
    encoding
        Encoding to use when opening a text file from a path.
        Ignored when `source` is content or in binary mode.

    Returns
    -------
    A file-like object. For content sources, this will be an
    `io.StringIO` or `io.BytesIO`. For file paths, this returns
    the standard file object.
    You can close the returned object by calling its `close()` method
    when done to release resources.
    """
    if isinstance(source, str):
        if fileex.path.is_path(source):
            return Path(source).open(mode=mode, encoding=encoding)
        return io.StringIO(source)
    if isinstance(source, bytes):
        return io.BytesIO(source)
    if isinstance(source, Path):
        return source.open(mode=mode, encoding=encoding)
    raise TypeError(
        f"Expected str, bytes, or pathlib.Path, got {type(source).__name__}"
    )


@overload
def content(
    file: FileLike,
    *,
    path_can_be_str: bool,
    output: Literal["str"] = "str",
    encoding: str = "utf-8",
    errors: str = "strict",
    preserve_pos: bool = True,
) -> str: ...

@overload
def content(
    file: FileLike,
    *,
    path_can_be_str: bool,
    output: Literal["bytes"],
    encoding: str = "utf-8",
    errors: str = "strict",
    preserve_pos: bool = True,
) -> bytes: ...

def content(
    file: FileLike,
    *,
    path_can_be_str: bool = True,
    output: Literal["str", "bytes"] = "str",
    encoding: str = "utf-8",
    errors: str = "strict",
    preserve_pos: bool = True,
) -> str | bytes:
    """Get the content of a file-like input.

    Parameters
    ----------
    file
        File-like input to get content from.
        - If an `os.PathLike` object is provided, it is interpreted as the path to the file.
        - If a string is provided and `path_can_be_str` is True, it is interpreted
          as the content of the file unless it is a valid existing file path,
          in which case it is treated as the path to the file.
        - If a string is provided and `path_can_be_str` is False,
          it is always treated as the content of the file.
        - If a bytes-like object is provided, it is interpreted as the content of the file.
        - If an object with a `read()` method is provided, it is treated as a file-like object.
    path_can_be_str
        If True, strings are checked to see if they are valid existing file paths.
        If so, they are treated as file paths; otherwise, as file content.
        If False, strings are always treated as file content.
    output
        Output type, either 'str' or 'bytes'.
    encoding
        Encoding used when converting between bytes and str.
    errors
        Error handling for encode/decode (e.g. 'strict', 'replace', 'ignore').
    preserve_pos
        If True and the object is seekable, restores the stream position after reading.

    Returns
    -------
    file_content
        Content of the file as a string or bytes.

    Raises
    -------
    ValueError
        If `output` is not 'str' or 'bytes'.
    TypeError
        If `file` is not a supported type.
    """
    def return_from_bytes(b: bytes) -> str | bytes:
        """Helper to return bytes or decoded str based on output parameter."""
        return b.decode(encoding, errors=errors) if output == "str" else b

    def return_from_str(s: str) -> str | bytes:
        """Helper to return str or encoded bytes based on output parameter."""
        return s if output == "str" else s.encode(encoding, errors=errors)

    if output not in ("str", "bytes"):
        raise ValueError("output must be either 'str' or 'bytes'")

    # Path: normalize to bytes via filesystem read
    if isinstance(file, os.PathLike):
        return return_from_bytes(Path(file).read_bytes())

    # String: check if path or content
    if isinstance(file, str):
        if path_can_be_str and fileex.path.is_path(file):
            return return_from_bytes(Path(file).read_bytes())
        return return_from_str(file)

    # Bytes-like: normalize to bytes
    if isinstance(file, (bytes, bytearray, memoryview)):
        return return_from_bytes(bytes(file))

    # Streams / file objects (open(...), BytesIO, sockets, etc.)
    if isinstance(file, ReadableFileLike):
        # Try to preserve cursor position if possible.
        pos: int | None = None
        if preserve_pos:
            try:
                pos = file.tell()  # type: ignore[attr-defined]
            except Exception:
                pos = None

        try:
            raw = file.read()
        finally:
            if preserve_pos and pos is not None:
                try:
                    file.seek(pos)  # type: ignore[attr-defined]
                except Exception:
                    pass

        if isinstance(raw, str):
            return return_from_str(raw)
        if isinstance(raw, (bytes, bytearray, memoryview)):
            return return_from_bytes(bytes(raw))

        raise TypeError(
            f"file.read() must return str or bytes, got {type(raw).__name__}"
        )

    raise TypeError(
        "Expected str, bytes-like, path-like, or a readable stream; "
        f"got {type(file).__name__}"
    )
