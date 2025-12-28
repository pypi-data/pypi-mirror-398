import os
from typing import Any

from ..._core.utils.write_yaml_list import write_yaml_list as _write_yaml_list


def write_yaml_list(
    file_path: str | os.PathLike[str],
    yaml_list: list[Any],
    *,
    allow_unicode: bool = True,
    sort_keys: bool = False,
) -> None:
    """
    Write YAML list data to a file

    Args:
        file_path (str | os.PathLike[str]): Path to the file to write
        yaml_list (list[Any]): YAML list data to write
        allow_unicode (bool): Whether to allow Unicode characters
        sort_keys (bool): Whether to sort keys
    """
    _write_yaml_list(
        "sync", file_path, yaml_list, allow_unicode=allow_unicode, sort_keys=sort_keys
    )
