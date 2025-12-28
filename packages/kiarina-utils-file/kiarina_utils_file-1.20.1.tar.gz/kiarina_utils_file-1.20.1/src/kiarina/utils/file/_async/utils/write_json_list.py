import os
from typing import Any

from ..._core.utils.write_json_list import write_json_list as _write_json_list


async def write_json_list(
    file_path: str | os.PathLike[str],
    json_list: list[Any],
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> None:
    """
    Write JSON list data to file asynchronously

    Args:
        file_path (str | os.PathLike[str]): Path to the file to write
        json_list (list[Any]): JSON list data to write
        indent (int): Indentation width
        ensure_ascii (bool): Whether to escape non-ASCII characters
        sort_keys (bool): Whether to sort keys
    """
    await _write_json_list(
        "async",
        file_path,
        json_list,
        indent=indent,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
    )
