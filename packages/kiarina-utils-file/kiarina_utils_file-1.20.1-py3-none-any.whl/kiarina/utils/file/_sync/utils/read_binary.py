import os
from typing import overload

from ..._core.utils.read_binary import read_binary as _read_binary


@overload
def read_binary(file_path: str | os.PathLike[str]) -> bytes | None: ...


@overload
def read_binary(file_path: str | os.PathLike[str], *, default: bytes) -> bytes: ...


def read_binary(
    file_path: str | os.PathLike[str], *, default: bytes | None = None
) -> bytes | None:
    """
    Read binary data from a file.

    Args:
        file_path (str | os.PathLike[str]): Path to the file to read
        default (bytes | None): Default value to return if file doesn't exist. Default is None

    Returns:
        (bytes | None): Binary data from the file. Returns default if file doesn't exist

    raises:
        IsADirectoryError: If the file is a directory
    """
    return _read_binary("sync", file_path, default=default)
