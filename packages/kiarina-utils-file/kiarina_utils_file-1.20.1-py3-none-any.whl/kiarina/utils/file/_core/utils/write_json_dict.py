import json
import os
from typing import Any, Awaitable, Literal, overload

from .write_text import write_text


@overload
def write_json_dict(
    mode: Literal["sync"],
    file_path: str | os.PathLike[str],
    json_dict: dict[str, Any],
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> None: ...


@overload
def write_json_dict(
    mode: Literal["async"],
    file_path: str | os.PathLike[str],
    json_dict: dict[str, Any],
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> Awaitable[None]: ...


def write_json_dict(
    mode: Literal["sync", "async"],
    file_path: str | os.PathLike[str],
    json_dict: dict[str, Any],
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> None | Awaitable[None]:
    """
    Write JSON dictionary data to a file

    Args:
        mode (Literal["sync", "async"]): Execution mode, either "sync" or "async"
        file_path (str | os.PathLike[str]): Path to the file to write
        json_dict (dict[str, Any]): JSON dictionary data to write
        indent (int): Indentation width
        ensure_ascii (bool): Whether to escape non-ASCII characters
        sort_keys (bool): Whether to sort keys
    """
    json_text = json.dumps(
        json_dict, indent=indent, ensure_ascii=ensure_ascii, sort_keys=sort_keys
    )

    def _sync() -> None:
        write_text("sync", file_path, json_text)

    def _async() -> Awaitable[None]:
        return write_text("async", file_path, json_text)

    if mode == "sync":
        _sync()
        return None
    else:
        return _async()
