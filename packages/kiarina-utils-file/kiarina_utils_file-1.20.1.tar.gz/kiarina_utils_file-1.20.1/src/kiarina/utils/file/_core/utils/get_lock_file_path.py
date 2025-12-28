import glob
import hashlib
import os
import random
import tempfile
import time
from unicodedata import normalize

from filelock import FileLock, Timeout

from ...settings import settings_manager


def get_lock_file_path(file_path: str | os.PathLike[str]) -> str:
    """
    Generate a lock file path for the given file path.

    Args:
        file_path: Path to the file that needs locking

    Returns:
        Path to the corresponding lock file

    Note:
        This function may trigger automatic cleanup of old lock files
        if enabled in settings.
    """
    norm = _normalize_path(file_path)
    digest = hashlib.sha256(norm.encode("utf-8", "surrogatepass")).hexdigest()
    base = _get_lock_base_dir()

    # Occasionally clean up old lock files (with low probability to avoid overhead)
    _maybe_cleanup_old_locks()

    # Use sharding to avoid too many files in a single directory
    subdir = os.path.join(base, digest[:2], digest[2:4])
    _ensure_dir(subdir)
    return os.path.join(subdir, f"{digest}.lock")


def _maybe_cleanup_old_locks() -> None:
    """
    Occasionally trigger cleanup of old lock files with controlled frequency.

    This is called with low probability to avoid performance overhead
    while ensuring old locks are eventually cleaned up. It includes
    protection against concurrent execution and excessive frequency.
    """
    settings = settings_manager.settings

    # Only cleanup if enabled and with 1% probability
    if not settings.lock_cleanup_enabled or random.random() >= 0.01:
        return

    try:
        base = _get_lock_base_dir()
    except OSError:
        return

    # Use a token file to control cleanup frequency and prevent concurrent execution
    token_path = os.path.join(base, "cleanup.token")
    token_lock_path = token_path + ".lock"
    min_interval_seconds = 10 * 60  # 10 minutes minimum interval

    # FileLock is always available as a dependency

    # Use a lock to prevent concurrent cleanup operations
    token_lock = FileLock(token_lock_path)
    try:
        token_lock.acquire(timeout=0)
    except Timeout:
        # Another process is already doing cleanup
        return

    try:
        # Check if enough time has passed since last cleanup
        last_cleanup_time = 0.0
        try:
            last_cleanup_time = os.path.getmtime(token_path)
        except FileNotFoundError:
            pass

        now = time.time()
        if now - last_cleanup_time < min_interval_seconds:
            return

        # Update token file timestamp before cleanup (in case we crash during cleanup)
        try:
            with open(token_path, "a"):
                os.utime(token_path, None)
        except Exception:
            pass

        # Perform the actual cleanup with limits to prevent excessive load
        max_age_seconds = settings.lock_max_age_hours * 3600
        max_remove = 2000  # Limit cleanup to prevent excessive I/O
        cleanup_old_lock_files(max_age_seconds=max_age_seconds, max_remove=max_remove)

    finally:
        try:
            token_lock.release()
        except Exception:
            pass


def _normalize_path(p: str | os.PathLike[str]) -> str:
    """
    Normalize file path for consistent lock file generation.

    Args:
        p: File path to normalize

    Returns:
        Normalized absolute path with consistent Unicode normalization
    """
    try:
        p = os.path.expandvars(os.path.expanduser(os.fspath(p)))
        p = os.path.abspath(p)

        # Try to resolve symlinks, but don't fail if it doesn't work
        try:
            p = os.path.realpath(p)
        except (OSError, ValueError):
            # realpath can fail on Windows with long paths or invalid characters
            pass

        # Apply normpath for all platforms for consistency
        p = os.path.normpath(p)

        # Apply normcase only on Windows for case-insensitive filesystems
        if os.name == "nt":
            p = os.path.normcase(p)

        # Apply Unicode normalization for consistent handling across platforms
        # This is especially important on macOS where filesystem may use NFD
        p = normalize("NFC", p)

        return p
    except Exception:
        # Fallback to basic normalization if anything fails
        try:
            return os.path.abspath(os.fspath(p))
        except Exception:
            # Last resort: use the path as-is
            return str(p)


def _get_lock_base_dir() -> str:
    """
    Get the base directory for lock files.

    Returns:
        Path to the lock base directory

    Note:
        If no custom lock_dir is configured, uses the system temp directory
        which may be user-specific (e.g., on macOS) or shared (e.g., on Linux).
        Users can specify their own lock_dir via settings for explicit control.
    """
    base = settings_manager.settings.lock_dir

    if not base:
        # Use shared lock directory - users can configure lock_dir if they need isolation
        base = os.path.join(tempfile.gettempdir(), "kiarina-utils-file-locks")

    _ensure_dir(base)
    return base


def _ensure_dir(d: str) -> None:
    """
    Ensure directory exists with appropriate permissions for shared use.

    Args:
        d: Directory path to create

    Raises:
        OSError: If directory creation fails

    Note:
        Uses 1777 permissions (sticky bit) for shared directories, similar to /tmp.
        This allows multiple users to create files but only owners can delete their files.
    """
    try:
        os.makedirs(d, exist_ok=True)
        # Set permissions similar to /tmp: sticky bit + world writable
        # This allows multiple users to create lock files but only owners can delete them
        try:
            os.chmod(d, 0o1777)
        except (OSError, PermissionError):
            # chmod might fail on some filesystems or with insufficient permissions
            # Fall back to more permissive permissions
            try:
                os.chmod(d, 0o755)
            except (OSError, PermissionError):
                # This is not critical, so we continue with default permissions
                pass
    except OSError as e:
        # Re-raise with more context
        raise OSError(f"Failed to create lock directory '{d}': {e}") from e


def cleanup_old_lock_files(
    max_age_seconds: int = 24 * 3600, max_remove: int | None = None
) -> int:
    """
    Clean up old lock files that exceed the specified age.

    Args:
        max_age_seconds: Maximum age in seconds for lock files to keep
        max_remove: Maximum number of files to remove in one cleanup run

    Returns:
        Number of lock files removed

    Note:
        This function is safe to call concurrently and will skip files
        that are currently in use or cannot be accessed. It uses non-blocking
        lock acquisition to safely detect files that are still in use.
    """
    try:
        base = _get_lock_base_dir()
    except OSError:
        # If we can't access the lock directory, return 0
        return 0

    # FileLock is always available as a dependency

    now = time.time()
    removed = 0

    try:
        lock_pattern = os.path.join(base, "**", "*.lock")
        for path in glob.glob(lock_pattern, recursive=True):
            try:
                # Check if file is old enough to remove
                if now - os.path.getmtime(path) <= max_age_seconds:
                    continue

                # Check if the lock is currently in use by trying to acquire it
                # with zero timeout (non-blocking)
                test_lock = FileLock(path)
                try:
                    test_lock.acquire(timeout=0)
                except Timeout:
                    # Lock is in use, skip this file
                    continue
                else:
                    # We acquired the lock, so it's not in use
                    try:
                        test_lock.release()
                    except Exception:
                        # Release might fail, but that's okay
                        pass

                # Safe to remove the file
                os.remove(path)
                removed += 1

                # Respect the maximum removal limit
                if max_remove is not None and removed >= max_remove:
                    break

            except (OSError, FileNotFoundError):
                # File might be already removed by another process
                continue
            except Exception:
                # Unexpected error, but don't fail the entire cleanup
                continue

        # Also try to remove empty subdirectories
        _cleanup_empty_dirs(base)

    except Exception:
        # If glob fails or any other unexpected error, just return what we managed to remove
        pass

    return removed


def _cleanup_empty_dirs(base_dir: str) -> None:
    """
    Remove empty subdirectories in the lock directory.

    Args:
        base_dir: Base lock directory path
    """
    try:
        for root, dirs, files in os.walk(base_dir, topdown=False):
            # Skip the base directory itself
            if root == base_dir:
                continue

            # Try to remove directory if it's empty
            try:
                if not files and not dirs:
                    os.rmdir(root)
            except OSError:
                # Directory not empty or permission denied
                continue
    except Exception:
        # Don't fail if cleanup of empty dirs fails
        pass
