import os
from functools import cached_property
from typing import Self

from kiarina.utils.ext import extract_extension
from kiarina.utils.mime import MIMEBlob


class FileBlob:
    """
    File Blob - A container for file data with MIME type detection and path information.

    FileBlob is a comprehensive data container that combines file path information with
    MIME-typed binary data, providing a unified interface for file operations and data
    manipulation. It extends the functionality of MIMEBlob by adding file system context
    and path-based operations.

    Key Features:
        - **File path management**: Stores and normalizes file paths with proper handling
        - **MIME type detection**: Automatic MIME type detection from content and file extensions
        - **Data format conversion**: Support for text, binary, Base64, and data URL formats
        - **Hash-based naming**: Content-addressable file naming using cryptographic hashes
        - **Extension handling**: Smart extension detection from both path and MIME type
        - **Binary/text detection**: Automatic classification of data as binary or text

    The class provides convenient properties for accessing data in different formats:
    - Text representation with automatic encoding detection
    - Base64 encoding for web/API usage
    - Data URLs for direct browser consumption
    - Hash-based file naming for content-addressable storage

    Args:
        file_path (str | os.PathLike[str]): Path to the file (normalized automatically)
        mime_blob (MIMEBlob | None): Pre-existing MIMEBlob instance. If None, creates new one
        mime_type (str | None): MIME type of the data. Required if mime_blob is None
        raw_data (bytes | None): Binary data. Used if mime_blob is None
        raw_text (str | None): Text data that will be UTF-8 encoded. Used if mime_blob is None

    Raises:
        ValueError: If mime_type is not provided when mime_blob is None

    Examples:
        >>> # Create from file path and MIME type
        >>> blob = FileBlob("/path/to/document.txt", mime_type="text/plain", raw_text="Hello World")
        >>> print(blob.file_path)  # "/path/to/document.txt"
        >>> print(blob.mime_type)  # "text/plain"
        >>> print(blob.ext)        # ".txt"

        >>> # Create from existing MIMEBlob
        >>> mime_blob = MIMEBlob("image/jpeg", raw_data=jpeg_bytes)
        >>> blob = FileBlob("/path/to/image.jpg", mime_blob=mime_blob)
        >>> print(blob.raw_base64_url)  # "data:image/jpeg;base64,..."

        >>> # Extension detection from path vs MIME type
        >>> blob = FileBlob("document", mime_type="text/plain", raw_text="content")
        >>> print(blob.ext)  # ".txt" (from MIME type since path has no extension)

        >>> # Hash-based file naming
        >>> blob = FileBlob("temp.txt", mime_type="text/plain", raw_text="Hello")
        >>> print(blob.hashed_file_name)  # "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3.txt"

    Note:
        - Extension detection prioritizes file path over MIME type when available
        - The class does not validate consistency between file path and MIME type
        - All MIMEBlob functionality is available through delegation
    """

    def __init__(
        self,
        file_path: str | os.PathLike[str],
        mime_blob: MIMEBlob | None = None,
        *,
        mime_type: str | None = None,
        raw_data: bytes | None = None,
        raw_text: str | None = None,
    ):
        """
        Initialize FileBlob instance
        """
        self._file_path: str = os.path.expanduser(
            os.path.expandvars(os.fspath(file_path))
        )
        """File path"""

        if mime_blob is None:
            if mime_type is None:
                raise ValueError("mime_type must be provided if mime_blob is None")

            mime_blob = MIMEBlob(mime_type, raw_data, raw_text=raw_text)

        self._mime_blob: MIMEBlob = mime_blob
        """MIMEBlob instance"""

    def __str__(self) -> str:
        """
        String representation
        """
        return f"FileBlob({self.file_path}, {self.mime_blob})"

    def __eq__(self, other: object) -> bool:
        """
        Equality comparison
        """
        return (
            isinstance(other, FileBlob)
            and self.file_path == other.file_path
            and self.mime_blob == other.mime_blob
        )

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def file_path(self) -> str:
        """
        File path
        """
        return self._file_path

    @property
    def mime_blob(self) -> MIMEBlob:
        """
        MIMEBlob instance
        """
        return self._mime_blob

    @property
    def mime_type(self) -> str:
        """
        MIME type of the file
        """
        return self.mime_blob.mime_type

    @property
    def raw_data(self) -> bytes:
        """
        Raw binary data of the file
        """
        return self.mime_blob.raw_data

    @property
    def raw_text(self) -> str:
        """
        Raw text data of the file, if available
        """
        return self.mime_blob.raw_text

    @property
    def raw_base64_str(self) -> str:
        """
        Base64 encoded string of the raw binary data
        """
        return self.mime_blob.raw_base64_str

    @property
    def raw_base64_url(self) -> str:
        """
        Base64 URL encoded string of the raw binary data
        """
        return self.mime_blob.raw_base64_url

    @property
    def hash_string(self) -> str:
        """
        Hash string of the raw binary data
        """
        return self.mime_blob.hash_string

    @cached_property
    def ext(self) -> str:
        """
        File extension

        Returns the file extension based on the file path or MIME type.
        If the file path does not contain an extension, it uses the MIME type.
        """
        if ext := extract_extension(self.file_path):
            return ext

        return self.mime_blob.ext

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
        return self.mime_blob.is_binary()

    def is_text(self) -> bool:
        """
        Check if data is text

        Returns:
            bool: True if data is text, False if it is binary
        """
        return self.mime_blob.is_text()

    def replace(
        self,
        *,
        file_path: str | os.PathLike[str] | None = None,
        mime_blob: MIMEBlob | None = None,
        mime_type: str | None = None,
        raw_data: bytes | None = None,
        raw_text: str | None = None,
    ) -> Self:
        """
        Replace properties
        """
        mime_blob = mime_blob or self.mime_blob

        if mime_type is not None or raw_data is not None or raw_text is not None:
            mime_blob = mime_blob.replace(
                mime_type=mime_type,
                raw_data=raw_data,
                raw_text=raw_text,
            )

        return self.__class__(
            file_path=file_path or self.file_path,
            mime_blob=mime_blob,
        )
