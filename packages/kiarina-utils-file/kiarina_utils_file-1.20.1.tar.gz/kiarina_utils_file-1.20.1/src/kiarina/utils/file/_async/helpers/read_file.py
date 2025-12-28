import os
from typing import overload

from ..._core.models.file_blob import FileBlob
from ..._core.operations.read_file import read_file as _read_file


@overload
async def read_file(
    file_path: str | os.PathLike[str],
    *,
    fallback_mime_type: str = "application/octet-stream",
) -> FileBlob | None: ...


@overload
async def read_file(
    file_path: str | os.PathLike[str],
    *,
    fallback_mime_type: str = "application/octet-stream",
    default: FileBlob,
) -> FileBlob: ...


async def read_file(
    file_path: str | os.PathLike[str],
    *,
    fallback_mime_type: str = "application/octet-stream",
    default: FileBlob | None = None,
) -> FileBlob | None:
    """
    Read a file and return a FileBlob.

    Args:
        file_path (str | os.PathLike[str]): Path to the file to read
        fallback_mime_type (str): Fallback MIME type if detection fails
        default (FileBlob | None): Default value to return if file doesn't exist. Default is None

    Returns:
        FileBlob | None: FileBlob instance or None if the file does not exist
    """
    return await _read_file(
        "async", file_path, fallback_mime_type=fallback_mime_type, default=default
    )
