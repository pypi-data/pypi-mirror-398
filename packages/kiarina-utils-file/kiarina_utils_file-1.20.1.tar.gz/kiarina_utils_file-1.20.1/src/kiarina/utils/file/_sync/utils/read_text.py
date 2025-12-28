import os
from typing import overload

from ..._core.utils.read_text import read_text as _read_text


@overload
def read_text(file_path: str | os.PathLike[str]) -> str | None: ...


@overload
def read_text(file_path: str | os.PathLike[str], *, default: str) -> str: ...


def read_text(
    file_path: str | os.PathLike[str], *, default: str | None = None
) -> str | None:
    """
    Read text file

    Args:
        file_path (str | os.PathLike[str]): Path to the file to read
        default (str | None): Default value to return if file doesn't exist

    Returns:
        str | None: File content. Returns default if file doesn't exist
    """
    return _read_text("sync", file_path, default=default)
