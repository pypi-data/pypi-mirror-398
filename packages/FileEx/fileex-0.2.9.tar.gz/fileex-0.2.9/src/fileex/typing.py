"""FileEx type-hint definitions.

This module defines type-hints used throughout the package.
"""

import os
from typing import TypeAlias, Protocol, runtime_checkable


@runtime_checkable
class ReadableFileLike(Protocol):
    """Protocol for file-like objects that can be read from."""
    def read(self, size: int = -1) -> str | bytes: ...


PathLike: TypeAlias = os.PathLike | str
"""A file path, either as a string or any `os.PathLike` object."""


BytesLike: TypeAlias = bytes | bytearray | memoryview
"""A bytes-like object."""


FileLike: TypeAlias = ReadableFileLike | PathLike | str | BytesLike
"""A file-like input.

- If an `os.PathLike` object is provided, it is interpreted as the path to a file.
- If a string is provided, it is interpreted as the content of the file
  unless it is a valid existing file path, in which case it is treated as the path to a file.
- If a bytes-like object is provided, it is interpreted as the content of the file.
- If a `ReadableFileLike` object is provided, its `read()` method will be used to read content.
"""
