import os

from ..._core.utils.write_binary import write_binary as _write_binary


async def write_binary(file_path: str | os.PathLike[str], raw_data: bytes) -> None:
    """
    Write binary data to a file

    Args:
        file_path (str | os.PathLike[str]): Path to the file to write
        raw_data (bytes): Binary data to write
    """
    await _write_binary("async", file_path, raw_data)
