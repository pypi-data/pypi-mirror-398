import json
import os
from typing import Any, Awaitable, Literal, overload

from .read_text import read_text


@overload
def read_json_dict(
    mode: Literal["sync"],
    file_path: str | os.PathLike[str],
    *,
    default: dict[str, Any] | None = None,
) -> dict[str, Any] | None: ...


@overload
def read_json_dict(
    mode: Literal["async"],
    file_path: str | os.PathLike[str],
    *,
    default: dict[str, Any] | None = None,
) -> Awaitable[dict[str, Any] | None]: ...


def read_json_dict(
    mode: Literal["sync", "async"],
    file_path: str | os.PathLike[str],
    *,
    default: dict[str, Any] | None = None,
) -> dict[str, Any] | None | Awaitable[dict[str, Any] | None]:
    """
    Read JSON dictionary file

    Args:
        mode (Literal["sync", "async"]): Execution mode, either "sync" or "async"
        file_path (str | os.PathLike[str]): Path to the file to read
        default (dict[str, Any] | None): Default value to return if file doesn't exist

    Returns:
        dict[str, Any] | None: File content. Returns default if file doesn't exist
    """

    def _after(raw_text: str | None) -> dict[str, Any] | None:
        if raw_text is None:
            return default

        data = json.loads(raw_text)

        if not isinstance(data, dict):
            raise json.JSONDecodeError("JSON data is not a dictionary", raw_text, 0)

        return data

    def _sync() -> dict[str, Any] | None:
        raw_text = read_text("sync", file_path)
        return _after(raw_text)

    async def _async() -> dict[str, Any] | None:
        raw_text = await read_text("async", file_path)
        return _after(raw_text)

    if mode == "sync":
        return _sync()
    else:
        return _async()
