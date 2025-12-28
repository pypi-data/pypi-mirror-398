import os

from ..._core.utils.remove_file import remove_file as _remove_file


async def remove_file(file_path: str | os.PathLike[str]) -> None:
    """
    Remove a file asynchronously

    Args:
        file_path (str | os.PathLike[str]): Path to the file to remove
    """
    await _remove_file("async", file_path)
