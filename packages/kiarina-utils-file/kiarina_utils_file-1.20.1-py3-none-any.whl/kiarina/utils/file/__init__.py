"""
File I/O utilities for reading and writing various file formats.

This module provides comprehensive synchronous file I/O operations with support for:
- **Multiple file formats**: Text, binary, JSON, YAML
- **Automatic encoding detection**: Smart handling of various text encodings
- **MIME type detection**: Automatic content type identification
- **Atomic operations**: Safe file writing with temporary files and locking
- **FileBlob container**: Unified file data container with metadata

Key Features:
    - **Format-specific readers/writers**: Dedicated functions for JSON, YAML, text, and binary
    - **High-level file operations**: `read_file()` and `write_file()` with FileBlob containers
    - **Encoding safety**: Automatic encoding detection and proper Unicode handling
    - **Thread safety**: File locking mechanisms prevent concurrent access issues
    - **Error handling**: Graceful handling of missing files with configurable defaults

Examples:
    >>> import kiarina.utils.file as kf
    >>>
    >>> # High-level file operations with FileBlob
    >>> blob = kf.read_file("document.txt")
    >>> if blob:
    >>>     print(f"Content: {blob.raw_text}")
    >>>     print(f"MIME type: {blob.mime_type}")
    >>>
    >>> # Format-specific operations
    >>> data = kf.read_json_dict("config.json", default={})
    >>> kf.write_yaml_dict("output.yaml", {"key": "value"})
    >>>
    >>> # Binary operations
    >>> raw_data = kf.read_binary("image.jpg")
    >>> if raw_data:
    >>>     kf.write_binary("copy.jpg", raw_data)

Available Functions:
    **High-level operations:**
    - `read_file()`, `write_file()`: FileBlob-based operations with MIME detection

    **Text operations:**
    - `read_text()`, `write_text()`: Plain text with encoding detection

    **Binary operations:**
    - `read_binary()`, `write_binary()`: Raw binary data

    **JSON operations:**
    - `read_json_dict()`, `write_json_dict()`: JSON dictionaries
    - `read_json_list()`, `write_json_list()`: JSON arrays

    **YAML operations:**
    - `read_yaml_dict()`, `write_yaml_dict()`: YAML dictionaries
    - `read_yaml_list()`, `write_yaml_list()`: YAML arrays

    **File management:**
    - `remove_file()`: Safe file deletion

Note:
    For async operations, use `kiarina.utils.file.asyncio` module which provides
    the same API with async/await support and non-blocking I/O.
"""

# pip install kiarina-utils-file
import logging
from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._core.models.file_blob import FileBlob
    from ._core.types.markdown_content import MarkdownContent
    from ._sync.helpers.read_file import read_file
    from ._sync.helpers.read_markdown import read_markdown
    from ._sync.helpers.write_file import write_file
    from ._sync.utils.read_binary import read_binary
    from ._sync.utils.read_json_dict import read_json_dict
    from ._sync.utils.read_json_list import read_json_list
    from ._sync.utils.read_text import read_text
    from ._sync.utils.read_yaml_dict import read_yaml_dict
    from ._sync.utils.read_yaml_list import read_yaml_list
    from ._sync.utils.remove_file import remove_file
    from ._sync.utils.write_binary import write_binary
    from ._sync.utils.write_json_dict import write_json_dict
    from ._sync.utils.write_json_list import write_json_list
    from ._sync.utils.write_text import write_text
    from ._sync.utils.write_yaml_dict import write_yaml_dict
    from ._sync.utils.write_yaml_list import write_yaml_list

__version__ = version("kiarina-utils-file")

__all__ = [
    # ._core.models
    "FileBlob",
    # ._core.types
    "MarkdownContent",
    # ._sync.helpers
    "read_file",
    "read_markdown",
    "write_file",
    # ._sync.utils
    "read_binary",
    "read_json_dict",
    "read_json_list",
    "read_text",
    "read_yaml_dict",
    "read_yaml_list",
    "remove_file",
    "write_binary",
    "write_json_dict",
    "write_json_list",
    "write_text",
    "write_yaml_dict",
    "write_yaml_list",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._core.models
        "FileBlob": "._core.models.file_blob",
        # ._core.types
        "MarkdownContent": "._core.types.markdown_content",
        # ._sync.helpers
        "read_file": "._sync.helpers.read_file",
        "read_markdown": "._sync.helpers.read_markdown",
        "write_file": "._sync.helpers.write_file",
        # ._sync.utils
        "read_binary": "._sync.utils.read_binary",
        "read_json_dict": "._sync.utils.read_json_dict",
        "read_json_list": "._sync.utils.read_json_list",
        "read_text": "._sync.utils.read_text",
        "read_yaml_dict": "._sync.utils.read_yaml_dict",
        "read_yaml_list": "._sync.utils.read_yaml_list",
        "remove_file": "._sync.utils.remove_file",
        "write_binary": "._sync.utils.write_binary",
        "write_json_dict": "._sync.utils.write_json_dict",
        "write_json_list": "._sync.utils.write_json_list",
        "write_text": "._sync.utils.write_text",
        "write_yaml_dict": "._sync.utils.write_yaml_dict",
        "write_yaml_list": "._sync.utils.write_yaml_list",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
