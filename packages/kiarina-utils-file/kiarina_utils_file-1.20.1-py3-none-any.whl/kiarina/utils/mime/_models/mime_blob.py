import base64
import hashlib
import logging
from functools import cached_property
from typing import Self

from kiarina.utils.encoding import (
    decode_binary_to_text,
    is_binary,
)
from kiarina.utils.ext import detect_extension

from ..settings import settings_manager

logger = logging.getLogger(__name__)


class MIMEBlob:
    """
    MIME Blob - A container for MIME-typed binary data

    A versatile data container that holds MIME type and binary data simultaneously,
    supporting data manipulation and conversion in various formats including text,
    Base64, data URLs, and file operations.

    This class provides convenient properties for accessing data in different formats:
    - Text representation with automatic encoding detection
    - Base64 encoding for web/API usage
    - Data URLs for direct browser consumption
    - Hash-based file naming for content-addressable storage

    Args:
        mime_type: MIME type of the data (e.g., 'text/plain', 'image/jpeg')
        raw_data: Binary data (mutually exclusive with raw_text)
        raw_text: Text data that will be UTF-8 encoded (mutually exclusive with raw_data)

    Example:
        >>> # Create from text
        >>> blob = MIMEBlob("text/plain", raw_text="Hello World")
        >>> print(blob.raw_text)  # "Hello World"
        >>> print(blob.ext)       # ".txt"

        >>> # Create from binary data
        >>> blob = MIMEBlob("image/jpeg", raw_data=jpeg_bytes)
        >>> print(blob.raw_base64_url)  # "data:image/jpeg;base64,..."

    Note:
        Consistency between MIME type and binary data is not guaranteed.
        The class trusts the provided MIME type and does not validate it
        against the actual data content.
    """

    def __init__(
        self,
        mime_type: str,
        raw_data: bytes | None = None,
        *,
        raw_text: str | None = None,
    ):
        """
        Initialize MIMEBlob

        Args:
            mime_type: MIME type of the data (e.g., 'text/plain', 'image/jpeg')
            raw_data: Binary data. If provided, this will be used as the data source.
            raw_text: Text data. If provided, it will be encoded to bytes using UTF-8.
                     This is a keyword-only argument.

        Raises:
            ValueError: If mime_type is empty, if neither raw_data nor raw_text is provided,
                       or if both raw_data and raw_text are provided.

        Note:
            Exactly one of raw_data or raw_text must be provided. If raw_text is provided,
            it will be cached for performance optimization.
        """
        if not mime_type:
            raise ValueError("MIME type is required")

        if raw_data is None and raw_text is None:
            raise ValueError("Either raw_data or raw_text must be provided")

        if raw_data is not None and raw_text is not None:
            raise ValueError("Only one of raw_data or raw_text should be provided")

        if raw_data is None:
            raw_data = (raw_text or "").encode("utf-8", errors="replace")

        self._mime_type: str = mime_type
        """MIME type"""

        self._raw_data: bytes = raw_data
        """Binary data"""

        # Cache raw_text if it was specified
        if raw_text is not None:
            self.__dict__["raw_text"] = raw_text

    def __str__(self) -> str:
        """
        String representation
        """
        return f"MIMEBlob({self.mime_type}, {len(self.raw_data)} bytes)"

    def __eq__(self, other: object) -> bool:
        """
        Equality comparison
        """
        return (
            isinstance(other, MIMEBlob)
            and self.mime_type == other.mime_type
            and self.raw_data == other.raw_data
        )

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def mime_type(self) -> str:
        """
        MIME type
        """
        return self._mime_type

    @property
    def raw_data(self) -> bytes:
        """
        Binary data
        """
        return self._raw_data

    @cached_property
    def raw_text(self) -> str:
        """
        Text data decoded from binary data

        Automatically decodes the binary data to text using appropriate encoding detection.
        If raw_text was provided during initialization, the cached value is returned.
        For empty data, returns an empty string.

        Returns:
            str: The decoded text representation of the binary data
        """
        return decode_binary_to_text(self.raw_data) if self.raw_data else ""

    @cached_property
    def raw_base64_str(self) -> str:
        """
        Binary data encoded as Base64 string

        Encodes the binary data using standard Base64 encoding and returns it as a UTF-8 string.
        The result is cached for performance, but be aware that large data may consume
        significant memory when cached.

        Returns:
            str: Base64 encoded string representation of the binary data

        Note:
            For large files, consider the memory implications of caching the Base64 string.
        """
        return base64.b64encode(self.raw_data).decode("utf-8")

    @property
    def raw_base64_url(self) -> str:
        """
        Binary data encoded as Base64 data URL

        Creates a data URL (RFC 2397) that can be directly used in web browsers
        or other applications that support data URLs. The format follows:
        data:{mime_type};base64,{base64_data}

        Returns:
            str: Complete data URL string with MIME type and Base64 encoded data

        Example:
            "data:text/plain;base64,SGVsbG8gV29ybGQ="

        Note:
            This property depends on raw_base64_str, so memory considerations
            for large files apply here as well.
        """
        return f"data:{self.mime_type};base64,{self.raw_base64_str}"

    @cached_property
    def hash_string(self) -> str:
        """
        Hash string of the binary data

        Computes a hash digest of the binary data using the configured hash algorithm.
        The hash algorithm is determined by the settings manager configuration.
        The result is cached for performance.

        Returns:
            str: Hexadecimal hash digest of the binary data

        Raises:
            ValueError: If the configured hash algorithm is not supported by hashlib

        Note:
            The hash algorithm used depends on the current settings configuration.
            Common algorithms include 'sha256', 'md5', 'sha1', etc.
        """
        hash_algorithm = settings_manager.settings.hash_algorithm

        if (h := getattr(hashlib, hash_algorithm, None)) is None:
            raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")

        hash_string = h(self.raw_data).hexdigest()
        assert isinstance(hash_string, str), "Hash string must be a string"
        return hash_string

    @cached_property
    def ext(self) -> str:
        """
        File extension based on MIME type

        Detects and returns the appropriate file extension based on the MIME type.
        If no extension can be determined from the MIME type, returns ".bin" as fallback.
        The result is cached for performance.

        Returns:
            str: File extension including the dot (e.g., '.txt', '.jpg', '.bin')

        Example:
            For MIME type 'text/plain' returns '.txt'
            For MIME type 'image/jpeg' returns '.jpg'
            For unknown MIME types returns '.bin'
        """
        return detect_extension(self.mime_type, default=".bin")

    @property
    def hashed_file_name(self) -> str:
        """
        Hash string-based filename

        Returns a filename consisting of hash string + extension.
        """
        return f"{self.hash_string}{self.ext}"

    # --------------------------------------------------
    # Methods
    # --------------------------------------------------

    def is_binary(self) -> bool:
        """
        Check if data is binary

        Returns:
            bool: True if data is binary, False if it is text
        """
        return is_binary(self.raw_data)

    def is_text(self) -> bool:
        """
        Check if data is text

        Returns:
            bool: True if data is text, False if it is binary
        """
        return not self.is_binary()

    def replace(
        self,
        *,
        mime_type: str | None = None,
        raw_data: bytes | None = None,
        raw_text: str | None = None,
    ) -> Self:
        """
        Replace properties of the MIMEBlob

        Args:
            mime_type: New MIME type to set (optional)
            raw_data: New binary data to set (optional)
            raw_text: New text data to set (optional)

        Returns:
            Self: A new instance of MIMEBlob with updated properties
        """
        if raw_data is not None and raw_text is not None:
            raise ValueError("Only one of raw_data or raw_text should be provided")

        if raw_data is None and raw_text is None:
            raw_data = self.raw_data

        return self.__class__(
            mime_type=mime_type or self.mime_type,
            raw_data=raw_data,
            raw_text=raw_text,
        )
