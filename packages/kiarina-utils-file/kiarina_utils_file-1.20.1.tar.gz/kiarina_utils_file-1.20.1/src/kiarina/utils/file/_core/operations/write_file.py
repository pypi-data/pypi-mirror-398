import os
from typing import Awaitable, Literal, overload

from ..models.file_blob import FileBlob
from ..utils.write_binary import write_binary


@overload
def write_file(
    mode: Literal["sync"],
    file_blob: FileBlob,
    file_path: str | os.PathLike[str] | None = None,
) -> None: ...


@overload
def write_file(
    mode: Literal["async"],
    file_blob: FileBlob,
    file_path: str | os.PathLike[str] | None = None,
) -> Awaitable[None]: ...


def write_file(
    mode: Literal["sync", "async"],
    file_blob: FileBlob,
    file_path: str | os.PathLike[str] | None = None,
) -> None | Awaitable[None]:
    """
    Write a FileBlob to a file

    Args:
        mode (Literal["sync", "async"]): Execution mode, either "sync" or "async"
        file_blob (FileBlob): The FileBlob instance to write
        file_path (str | os.PathLike[str] | None): Path to the file to write. If None, uses the FileBlob's path

    Returns:
        Awaitable[None] | None: None if successful, or an awaitable if in async mode
    """
    if file_path is None:
        file_path = file_blob.file_path

    def _sync() -> None:
        write_binary("sync", file_path, file_blob.raw_data)

    async def _async() -> None:
        await write_binary("async", file_path, file_blob.raw_data)

    if mode == "sync":
        _sync()
        return None
    else:
        return _async()
