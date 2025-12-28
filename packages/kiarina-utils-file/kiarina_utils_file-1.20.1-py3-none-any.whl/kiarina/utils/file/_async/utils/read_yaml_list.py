import os
from typing import Any, overload

from ..._core.utils.read_yaml_list import read_yaml_list as _read_yaml_list


@overload
async def read_yaml_list(
    file_path: str | os.PathLike[str],
) -> list[Any] | None: ...


@overload
async def read_yaml_list(
    file_path: str | os.PathLike[str], *, default: list[Any]
) -> list[Any]: ...


async def read_yaml_list(
    file_path: str | os.PathLike[str], *, default: list[Any] | None = None
) -> list[Any] | None:
    """
    Read YAML list file asynchronously

    Args:
        file_path (str | os.PathLike[str]): Path to the file to read
        default (list[Any] | None): Default value to return if the file does not exist

    Returns:
        list[Any] | None: File content. Returns default if the file does not exist
    """
    return await _read_yaml_list("async", file_path, default=default)
