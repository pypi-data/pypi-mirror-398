import os

from ..._core.utils.remove_file import remove_file as _remove_file


def remove_file(file_path: str | os.PathLike[str]) -> None:
    """
    Remove a file

    Args:
        file_path (str | os.PathLike[str]): Path to the file to remove
    """
    _remove_file("sync", file_path)
