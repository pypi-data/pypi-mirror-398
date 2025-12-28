import os
from typing import Any, overload

from ..._core.utils.read_yaml_dict import read_yaml_dict as _read_yaml_dict


@overload
def read_yaml_dict(file_path: str | os.PathLike[str]) -> dict[str, Any] | None: ...


@overload
def read_yaml_dict(
    file_path: str | os.PathLike[str], *, default: dict[str, Any]
) -> dict[str, Any]: ...


def read_yaml_dict(
    file_path: str | os.PathLike[str], *, default: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """
    Read YAML dictionary file

    Args:
        file_path (str | os.PathLike[str]): Path to the file to read
        default (dict[str, Any] | None): Default value to return if file doesn't exist

    Returns:
        dict[str, Any] | None: File content. Returns default if file doesn't exist
    """
    return _read_yaml_dict("sync", file_path, default=default)
