import os
from typing import Awaitable, Literal, overload

import aiofiles
from filelock import AsyncFileLock, FileLock

from .get_lock_file_path import get_lock_file_path


@overload
def read_binary(
    mode: Literal["sync"],
    file_path: str | os.PathLike[str],
    *,
    default: bytes | None = None,
) -> bytes | None: ...


@overload
def read_binary(
    mode: Literal["async"],
    file_path: str | os.PathLike[str],
    *,
    default: bytes | None = None,
) -> Awaitable[bytes | None]: ...


def read_binary(
    mode: Literal["sync", "async"],
    file_path: str | os.PathLike[str],
    *,
    default: bytes | None = None,
) -> bytes | None | Awaitable[bytes | None]:
    """
    Read binary data from a file with locking mechanism.

    Args:
        mode (Literal["sync", "async"]): Execution mode, either "sync" or "async"
        file_path (str | os.PathLike[str]): Path to the file to read
        default (bytes | None): Default value to return if file doesn't exist. Default is None

    Returns:
        bytes | None | Awaitable[bytes | None]: The binary data read from the file, or default if file doesn't exist

    raises:
        IsADirectoryError: If the file is a directory
    """
    # Normalize the file path and resolve symlinks
    file_path = os.path.expanduser(os.path.expandvars(os.fspath(file_path)))

    # Resolve symlinks to get the actual file path
    # This ensures that locks are taken on the real file, not the symlink
    if os.path.lexists(file_path):  # Check if path exists (including broken symlinks)
        file_path = os.path.realpath(file_path)

    # Define the lock file path
    lock_file_path = get_lock_file_path(file_path)

    # Function to check if the file exists and is not a directory
    def _check_file_exists() -> bool:
        if not os.path.exists(file_path):
            return False

        if os.path.isdir(file_path):
            raise IsADirectoryError(f"{file_path} is a directory")

        return True

    # Synchronous version of the function
    def _sync() -> bytes | None:
        lock = FileLock(lock_file_path)

        with lock:
            if not _check_file_exists():
                return default

            with open(file_path, "rb") as f:
                return f.read()

    # Asynchronous version of the function
    async def _async() -> bytes | None:
        lock = AsyncFileLock(lock_file_path)

        async with lock:
            if not _check_file_exists():
                return default

            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()

    # Return the appropriate function based on the mode
    if mode == "sync":
        return _sync()
    else:
        return _async()
