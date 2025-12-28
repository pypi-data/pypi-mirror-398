import os
from typing import Awaitable, Literal, overload

from filelock import AsyncFileLock, FileLock

from .get_lock_file_path import get_lock_file_path


@overload
def remove_file(
    mode: Literal["sync"],
    file_path: str | os.PathLike[str],
) -> None: ...


@overload
def remove_file(
    mode: Literal["async"],
    file_path: str | os.PathLike[str],
) -> Awaitable[None]: ...


def remove_file(
    mode: Literal["sync", "async"],
    file_path: str | os.PathLike[str],
) -> None | Awaitable[None]:
    """
    Remove a file with locking mechanism.

    Args:
        mode (Literal["sync", "async"]): Execution mode, either "sync" or "async"
        file_path (str | os.PathLike[str]): Path to the file to remove
    """
    # Normalize the file path
    file_path = os.path.expanduser(os.path.expandvars(os.fspath(file_path)))

    # Define the lock file path
    lock_file_path = get_lock_file_path(file_path)

    # Synchronous version of the function
    def _sync() -> None:
        lock = FileLock(lock_file_path)

        with lock:
            if os.path.exists(file_path):
                os.remove(file_path)

    # Asynchronous version of the function
    async def _async() -> None:
        lock = AsyncFileLock(lock_file_path)

        async with lock:
            if os.path.exists(file_path):
                os.remove(file_path)

    # Return the appropriate function based on the mode
    if mode == "sync":
        _sync()
        return None
    else:
        return _async()
