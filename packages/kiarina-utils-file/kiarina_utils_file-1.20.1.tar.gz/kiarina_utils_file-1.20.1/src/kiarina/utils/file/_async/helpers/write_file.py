import os

from ..._core.models.file_blob import FileBlob
from ..._core.operations.write_file import write_file as _write_file


async def write_file(
    file_blob: FileBlob,
    file_path: str | os.PathLike[str] | None = None,
) -> None:
    """
    Write a FileBlob to a file.

    Args:
        file_blob (FileBlob): The FileBlob instance to write
        file_path (str | os.PathLike[str] | None): Path to the file to write. If None, uses the FileBlob's path

    Returns:
        None
    """
    await _write_file("async", file_blob, file_path=file_path)
