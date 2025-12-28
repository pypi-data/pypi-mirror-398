import os
from typing import overload

from ..._core.utils.read_text import read_text as _read_text


@overload
async def read_text(file_path: str | os.PathLike[str]) -> str | None: ...


@overload
async def read_text(file_path: str | os.PathLike[str], *, default: str) -> str: ...


async def read_text(
    file_path: str | os.PathLike[str], *, default: str | None = None
) -> str | None:
    """
    Read text file

    Args:
        file_path (str | os.PathLike[str]): Path to the file to read
        default (str | None): Default value to return if the file does not exist

    Returns:
        str | None: File content. Returns default if the file does not exist
    """
    return await _read_text("async", file_path, default=default)
