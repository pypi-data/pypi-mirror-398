import os

from ..._core.utils.write_text import write_text as _write_text


def write_text(file_path: str | os.PathLike[str], raw_text: str) -> None:
    """
    Write text to a file

    Args:
        file_path (str | os.PathLike[str]): Path to the file to write
        raw_text (str): Text to write
    """
    _write_text("sync", file_path, raw_text)
