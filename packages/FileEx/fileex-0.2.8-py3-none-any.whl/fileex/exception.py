from pathlib import Path as _Path


class FileExError(Exception):
    """Base class for all FileEx errors."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
        return


class FileExInputError(FileExError):
    """Error in the input arguments provided to FileEx methods."""
    def __init__(self, message: str):
        super().__init__(message)
        return


class FileExPathNotFoundError(FileExError):
    """The given path does not exist."""
    def __init__(self, path: _Path, is_dir: bool):
        self.path = path
        message = f"No {'directory' if is_dir else 'file'} found at '{path}'."
        super().__init__(message)
        return
