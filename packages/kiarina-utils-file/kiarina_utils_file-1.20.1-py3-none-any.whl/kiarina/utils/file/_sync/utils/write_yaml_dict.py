import os
from typing import Any

from ..._core.utils.write_yaml_dict import write_yaml_dict as _write_yaml_dict


def write_yaml_dict(
    file_path: str | os.PathLike[str],
    yaml_dict: dict[str, Any],
    *,
    allow_unicode: bool = True,
    sort_keys: bool = False,
) -> None:
    """
    Write YAML dictionary data to a file

    Args:
        file_path (str | os.PathLike[str]): Path to the file to write
        yaml_dict (dict[str, Any]): YAML dictionary data to write
        allow_unicode (bool): Whether to allow Unicode characters
        sort_keys (bool): Whether to sort keys
    """
    _write_yaml_dict(
        "sync", file_path, yaml_dict, allow_unicode=allow_unicode, sort_keys=sort_keys
    )
