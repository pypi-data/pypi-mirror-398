"""
Asynchronous file I/O utilities for reading and writing various file formats.

This module provides comprehensive asynchronous file I/O operations with support for:
- **Multiple file formats**: Text, binary, JSON, YAML
- **Automatic encoding detection**: Smart handling of various text encodings
- **MIME type detection**: Automatic content type identification
- **Atomic operations**: Safe file writing with temporary files and async locking
- **FileBlob container**: Unified file data container with metadata
- **Non-blocking I/O**: Full async/await support for high-performance applications

Key Features:
    - **Format-specific readers/writers**: Dedicated async functions for JSON, YAML, text, and binary
    - **High-level file operations**: `read_file()` and `write_file()` with FileBlob containers
    - **Encoding safety**: Automatic encoding detection and proper Unicode handling
    - **Async thread safety**: Async file locking mechanisms prevent concurrent access issues
    - **Error handling**: Graceful handling of missing files with configurable defaults
    - **Performance optimized**: Non-blocking I/O operations for scalable applications

Examples:
    >>> import kiarina.utils.file.asyncio as kfa
    >>>
    >>> # High-level async file operations with FileBlob
    >>> blob = await kfa.read_file("document.txt")
    >>> if blob:
    >>>     print(f"Content: {blob.raw_text}")
    >>>     print(f"MIME type: {blob.mime_type}")
    >>>
    >>> # Format-specific async operations
    >>> data = await kfa.read_json_dict("config.json", default={})
    >>> await kfa.write_yaml_dict("output.yaml", {"key": "value"})
    >>>
    >>> # Binary async operations
    >>> raw_data = await kfa.read_binary("image.jpg")
    >>> if raw_data:
    >>>     await kfa.write_binary("copy.jpg", raw_data)

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
    - `remove_file()`: Safe async file deletion

Runtime Requirements:
    This module requires an async runtime (asyncio, trio, etc.). All functions
    must be called with `await` from within an async context.

Note:
    For synchronous operations, use the main `kiarina.utils.file` module instead.
    The API is identical except for the async/await requirement.
"""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._async.helpers.read_file import read_file
    from ._async.helpers.read_markdown import read_markdown
    from ._async.helpers.write_file import write_file
    from ._async.utils.read_binary import read_binary
    from ._async.utils.read_json_dict import read_json_dict
    from ._async.utils.read_json_list import read_json_list
    from ._async.utils.read_text import read_text
    from ._async.utils.read_yaml_dict import read_yaml_dict
    from ._async.utils.read_yaml_list import read_yaml_list
    from ._async.utils.remove_file import remove_file
    from ._async.utils.write_binary import write_binary
    from ._async.utils.write_json_dict import write_json_dict
    from ._async.utils.write_json_list import write_json_list
    from ._async.utils.write_text import write_text
    from ._async.utils.write_yaml_dict import write_yaml_dict
    from ._async.utils.write_yaml_list import write_yaml_list
    from ._core.models.file_blob import FileBlob
    from ._core.types.markdown_content import MarkdownContent

__all__ = [
    # ._async.helpers
    "read_file",
    "read_markdown",
    "write_file",
    # ._async.utils
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
    # ._core.models
    "FileBlob",
    # ._core.types
    "MarkdownContent",
]


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._async.helpers
        "read_file": "._async.helpers.read_file",
        "read_markdown": "._async.helpers.read_markdown",
        "write_file": "._async.helpers.write_file",
        # ._async.utils
        "read_binary": "._async.utils.read_binary",
        "read_json_dict": "._async.utils.read_json_dict",
        "read_json_list": "._async.utils.read_json_list",
        "read_text": "._async.utils.read_text",
        "read_yaml_dict": "._async.utils.read_yaml_dict",
        "read_yaml_list": "._async.utils.read_yaml_list",
        "remove_file": "._async.utils.remove_file",
        "write_binary": "._async.utils.write_binary",
        "write_json_dict": "._async.utils.write_json_dict",
        "write_json_list": "._async.utils.write_json_list",
        "write_text": "._async.utils.write_text",
        "write_yaml_dict": "._async.utils.write_yaml_dict",
        "write_yaml_list": "._async.utils.write_yaml_list",
        # ._core.models
        "FileBlob": "._core.models.file_blob",
        # ._core.types
        "MarkdownContent": "._core.types.markdown_content",
    }

    parent = __name__.rsplit(".", 1)[0]
    globals()[name] = getattr(import_module(module_map[name], parent), name)
    return globals()[name]
