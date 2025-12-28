import os
from typing import Awaitable, Literal, overload

from kiarina.utils.encoding import decode_binary_to_text

from .read_binary import read_binary


@overload
def read_text(
    mode: Literal["sync"],
    file_path: str | os.PathLike[str],
    *,
    default: str | None = None,
) -> str | None: ...


@overload
def read_text(
    mode: Literal["async"],
    file_path: str | os.PathLike[str],
    *,
    default: str | None = None,
) -> Awaitable[str | None]: ...


def read_text(
    mode: Literal["sync", "async"],
    file_path: str | os.PathLike[str],
    *,
    default: str | None = None,
) -> str | None | Awaitable[str | None]:
    """
    Read text file

    Args:
        mode (Literal["sync", "async"]): Execution mode, either "sync" or "async"
        file_path (str | os.PathLike[str]): Path to the file to read
        default (str | None): Default value to return if file doesn't exist

    Returns:
        str | None: File content. Returns default if file doesn't exist
    """

    def _after(raw_data: bytes | None) -> str | None:
        if raw_data is None:
            return default

        if not raw_data:
            return ""

        return decode_binary_to_text(raw_data)

    def _sync() -> str | None:
        raw_data = read_binary("sync", file_path)
        return _after(raw_data)

    async def _async() -> str | None:
        raw_data = await read_binary("async", file_path)
        return _after(raw_data)

    if mode == "sync":
        return _sync()
    else:
        return _async()
