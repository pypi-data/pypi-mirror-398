from typing import NotRequired, TypedDict


class MimeDetectionOptions(TypedDict, total=False):
    """
    Options for MIME type detection.

    All fields are optional and will be merged with default settings when provided.

    Attributes:
        mime_aliases: Custom MIME type aliases for normalization.
            Example: {"application/x-yaml": "application/yaml"}
        custom_mime_types: Custom extension to MIME type mapping.
            Example: {".myext": "application/x-custom"}
        multi_extensions: Multi-part extensions to recognize (e.g., {".tar.gz"}).
        archive_extensions: Archive-related extensions (e.g., {".tar"}).
        compression_extensions: Compression-related extensions (e.g., {".gz", ".bz2"}).
        encryption_extensions: Encryption-related extensions (e.g., {".gpg"}).
    """

    mime_aliases: NotRequired[dict[str, str]]
    custom_mime_types: NotRequired[dict[str, str]]
    multi_extensions: NotRequired[set[str]]
    archive_extensions: NotRequired[set[str]]
    compression_extensions: NotRequired[set[str]]
    encryption_extensions: NotRequired[set[str]]
