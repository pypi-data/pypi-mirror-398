import logging
import subprocess
import threading

from ..settings import settings_manager

logger = logging.getLogger(__name__)

_nkf_available: bool | None = None
"""Whether nkf command is available"""

_nkf_lock = threading.Lock()
"""Lock for thread-safe access to _nkf_available"""


def detect_with_nkf(raw_data: bytes) -> str | None:
    """
    Detect encoding using the nkf command

    For large files, only a sample from the beginning is used for efficiency.
    The sample size can be configured via settings.

    Args:
        raw_data (bytes): Binary data to detect encoding from

    Returns:
        (str | None): Detected encoding name (lowercase), or None if detection fails
    """
    global _nkf_available

    with _nkf_lock:
        if _nkf_available is False:
            return None

    if not raw_data:
        return None

    # Use sample for large files to improve performance
    max_size = settings_manager.settings.max_sample_size

    if len(raw_data) > max_size:
        sample_data = raw_data[:max_size]
        logger.debug(
            f"Using sample of {len(sample_data)} bytes from {len(raw_data)} bytes for nkf detection"
        )
    else:
        sample_data = raw_data

    try:
        result = subprocess.run(
            ["nkf", "-g"], input=sample_data, capture_output=True, text=False
        )
        detected = result.stdout.decode("utf-8").strip()

        with _nkf_lock:
            if _nkf_available is None:
                _nkf_available = True

        # Text files with BOM or emoji may also be detected as BINARY
        # Therefore, treat BINARY detection as undetectable
        if detected != "BINARY":
            return detected.lower()

    except FileNotFoundError:
        with _nkf_lock:
            _nkf_available = False

        logger.warning(
            "Warning: nkf command not found. For more accurate encoding detection, we recommend installing nkf.\n"
            "For macOS: brew install nkf\n"
            "For Ubuntu: sudo apt-get install nkf\n"
            "Using alternative detection methods."
        )

    except Exception as e:
        logger.debug(f"Failed to detect encoding with nkf: {e}")

    return None
