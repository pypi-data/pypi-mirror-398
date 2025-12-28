import os
from typing import overload

from ..._core.utils.read_binary import read_binary as _read_binary


@overload
async def read_binary(file_path: str | os.PathLike[str]) -> bytes | None: ...


@overload
async def read_binary(
    file_path: str | os.PathLike[str], *, default: bytes
) -> bytes: ...


async def read_binary(
    file_path: str | os.PathLike[str], *, default: bytes | None = None
) -> bytes | None:
    """
    Read binary data from a file

    Args:
        file_path (str | os.PathLike[str]): Path to the file to read
        default (bytes | None): Default value to return if the file does not exist. Default is None

    Returns:
        (bytes | None): Binary data of the file. Returns default if the file does not exist

    raises:
        IsADirectoryError: If the file is a directory
    """
    return await _read_binary("async", file_path, default=default)
