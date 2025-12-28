# kiarina-utils-file

A comprehensive Python library for file I/O operations with automatic encoding detection, MIME type detection, and support for various file formats.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

### 🚀 **Comprehensive File I/O**
- **Multiple file formats**: Text, binary, JSON, YAML
- **Sync & Async support**: Full async/await support for high-performance applications
- **Atomic operations**: Safe file writing with temporary files and locking
- **Thread safety**: File locking mechanisms prevent concurrent access issues

### 🔍 **Smart Detection**
- **Automatic encoding detection**: Smart handling of various text encodings with nkf support
- **MIME type detection**: Automatic content type identification using multiple detection methods
- **Extension handling**: Support for complex multi-part extensions (.tar.gz, .tar.gz.gpg)

### 📦 **Data Containers**
- **FileBlob**: Unified file data container with metadata and path information
- **MIMEBlob**: MIME-typed binary data container with format conversion support
- **Hash-based naming**: Content-addressable file naming using cryptographic hashes

### 🛡️ **Production Ready**
- **Error handling**: Graceful handling of missing files with configurable defaults
- **Performance optimized**: Non-blocking I/O operations and efficient caching
- **Type safety**: Full type hints and comprehensive testing

## Installation

```bash
pip install kiarina-utils-file
```

### Optional Dependencies

For enhanced functionality, install optional dependencies:

```bash
# For MIME type detection from file content
pip install kiarina-utils-file[mime]

# Or install with all optional dependencies
pip install kiarina-utils-file[all]
```

## Quick Start

### Basic File Operations

```python
import kiarina.utils.file as kf

# Read and write text files with automatic encoding detection
text = kf.read_text("document.txt", default="")
kf.write_text("output.txt", "Hello, World! 🌍")

# Binary file operations
data = kf.read_binary("image.jpg")
if data:
    kf.write_binary("copy.jpg", data)

# JSON operations with type safety
config = kf.read_json_dict("config.json", default={})
kf.write_json_dict("output.json", {"key": "value"})

# YAML operations
settings = kf.read_yaml_dict("settings.yaml", default={})
kf.write_yaml_list("list.yaml", [1, 2, 3])
```

### High-Level FileBlob Operations

```python
import kiarina.utils.file as kf

# Read file with automatic MIME type detection
blob = kf.read_file("document.pdf")
if blob:
    print(f"File: {blob.file_path}")
    print(f"MIME type: {blob.mime_type}")
    print(f"Size: {len(blob.raw_data)} bytes")
    print(f"Extension: {blob.ext}")

# Create and write FileBlob
blob = kf.FileBlob(
    "output.txt",
    mime_type="text/plain",
    raw_text="Hello, World!"
)
kf.write_file(blob)

# Data URL generation for web use
print(blob.raw_base64_url)  # data:text/plain;base64,SGVsbG8sIFdvcmxkIQ==
```

### Async Operations

```python
import kiarina.utils.file.asyncio as kfa

async def process_files():
    # All operations have async equivalents
    text = await kfa.read_text("large_file.txt")
    await kfa.write_json_dict("result.json", {"processed": True})

    # FileBlob operations
    blob = await kfa.read_file("document.pdf")
    if blob:
        await kfa.write_file(blob, "backup.pdf")
```

### MIME Type and Extension Detection

```python
import kiarina.utils.mime as km
import kiarina.utils.ext as ke

# MIME type detection - extension takes precedence
mime_type = km.detect_mime_type(
    file_name_hint="document.md",  # Extension is prioritized
    raw_data=file_data,
)
# Returns "text/markdown" even if content looks like plain text

# Content-based detection (fallback when no extension)
mime_type = km.detect_mime_type(raw_data=jpeg_data)  # "image/jpeg"

# Extension detection from MIME type
extension = ke.detect_extension("application/json")  # ".json"

# Multi-part extension extraction
extension = ke.extract_extension("archive.tar.gz")  # ".tar.gz"

# Create MIME blob from data
blob = km.create_mime_blob(jpeg_data)
print(f"Detected: {blob.mime_type}")  # "image/jpeg"
```

### Encoding Detection

```python
import kiarina.utils.encoding as kenc

# Automatic encoding detection
with open("mystery_file.txt", "rb") as f:
    raw_data = f.read()

encoding = kenc.detect_encoding(raw_data)
text = kenc.decode_binary_to_text(raw_data)

# Check if data is binary or text
is_binary = kenc.is_binary(raw_data)
```

## Advanced Usage

### Custom Configuration

Configure behavior through environment variables:

```bash
# Encoding detection
export KIARINA_UTILS_ENCODING_USE_NKF=true
export KIARINA_UTILS_ENCODING_DEFAULT_ENCODING=utf-8

# File operations
export KIARINA_UTILS_FILE_LOCK_DIR=/custom/lock/dir
export KIARINA_UTILS_FILE_LOCK_CLEANUP_ENABLED=true

# MIME type detection
export KIARINA_UTILS_MIME_HASH_ALGORITHM=sha256
```

### Error Handling

```python
import kiarina.utils.file as kf

try:
    data = kf.read_json_dict("config.json")
    if data is None:
        print("File not found, using defaults")
        data = {"default": True}
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Performance Considerations

```python
import kiarina.utils.file.asyncio as kfa

# For I/O intensive operations, use async versions
async def process_many_files(file_paths):
    tasks = [kfa.read_file(path) for path in file_paths]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]

# Use appropriate defaults to avoid None checks
config = kf.read_json_dict("config.json", default={})
# Instead of:
# config = kf.read_json_dict("config.json")
# if config is None:
#     config = {}
```

## API Reference

### File Operations

#### Synchronous API (`kiarina.utils.file`)

**High-level operations:**
- `read_file(path, *, fallback_mime_type="application/octet-stream", default=None) -> FileBlob | None`
- `write_file(file_blob, file_path=None) -> None`

**Text operations:**
- `read_text(path, *, default=None) -> str | None`
- `write_text(path, text) -> None`

**Binary operations:**
- `read_binary(path, *, default=None) -> bytes | None`
- `write_binary(path, data) -> None`

**JSON operations:**
- `read_json_dict(path, *, default=None) -> dict[str, Any] | None`
- `write_json_dict(path, data, *, indent=2, ensure_ascii=False, sort_keys=False) -> None`
- `read_json_list(path, *, default=None) -> list[Any] | None`
- `write_json_list(path, data, *, indent=2, ensure_ascii=False, sort_keys=False) -> None`

**YAML operations:**
- `read_yaml_dict(path, *, default=None) -> dict[str, Any] | None`
- `write_yaml_dict(path, data, *, allow_unicode=True, sort_keys=False) -> None`
- `read_yaml_list(path, *, default=None) -> list[Any] | None`
- `write_yaml_list(path, data, *, allow_unicode=True, sort_keys=False) -> None`

**File management:**
- `remove_file(path) -> None`

#### Asynchronous API (`kiarina.utils.file.asyncio`)

All synchronous functions have async equivalents with the same signatures, but they return `Awaitable` objects and must be called with `await`.

### Data Containers

#### FileBlob

```python
class FileBlob:
    def __init__(self, file_path, mime_blob=None, *, mime_type=None, raw_data=None, raw_text=None)

    # Properties
    file_path: str
    mime_blob: MIMEBlob
    mime_type: str
    raw_data: bytes
    raw_text: str
    raw_base64_str: str
    raw_base64_url: str
    hash_string: str
    ext: str
    hashed_file_name: str

    # Methods
    def is_binary() -> bool
    def is_text() -> bool
    def replace(*, file_path=None, mime_blob=None, mime_type=None, raw_data=None, raw_text=None) -> FileBlob
```

#### MIMEBlob

```python
class MIMEBlob:
    def __init__(self, mime_type, raw_data=None, *, raw_text=None)

    # Properties
    mime_type: str
    raw_data: bytes
    raw_text: str
    raw_base64_str: str
    raw_base64_url: str
    hash_string: str
    ext: str
    hashed_file_name: str

    # Methods
    def is_binary() -> bool
    def is_text() -> bool
    def replace(*, mime_type=None, raw_data=None, raw_text=None) -> MIMEBlob
```

### Utility Functions

#### MIME Type Detection (`kiarina.utils.mime`)

- `detect_mime_type(*, raw_data=None, stream=None, file_name_hint=None, **kwargs) -> str | None`
- `create_mime_blob(raw_data, *, fallback_mime_type="application/octet-stream") -> MIMEBlob`
- `apply_mime_alias(mime_type, *, mime_aliases=None) -> str`

#### Extension Detection (`kiarina.utils.ext`)

- `detect_extension(mime_type, *, custom_extensions=None, default=None) -> str | None`
- `extract_extension(file_name_hint, *, multi_extensions=None, **kwargs, default=None) -> str | None`

#### Encoding Detection (`kiarina.utils.encoding`)

- `detect_encoding(raw_data, *, use_nkf=None, **kwargs) -> str | None`
- `decode_binary_to_text(raw_data, *, use_nkf=None, **kwargs) -> str`
- `is_binary(raw_data, *, use_nkf=None, **kwargs) -> bool`
- `get_default_encoding() -> str`
- `normalize_newlines(text) -> str`

## Configuration

### Environment Variables

#### Encoding Detection
- `KIARINA_UTILS_ENCODING_USE_NKF`: Enable/disable nkf usage (bool)
- `KIARINA_UTILS_ENCODING_DEFAULT_ENCODING`: Default encoding (default: "utf-8")
- `KIARINA_UTILS_ENCODING_FALLBACK_ENCODINGS`: Comma-separated list of fallback encodings
- `KIARINA_UTILS_ENCODING_MAX_SAMPLE_SIZE`: Maximum bytes to sample for detection (default: 8192)
- `KIARINA_UTILS_ENCODING_CHARSET_NORMALIZER_CONFIDENCE_THRESHOLD`: Confidence threshold (default: 0.6)

#### File Operations
- `KIARINA_UTILS_FILE_LOCK_DIR`: Custom lock directory path
- `KIARINA_UTILS_FILE_LOCK_CLEANUP_ENABLED`: Enable automatic cleanup (default: true)
- `KIARINA_UTILS_FILE_LOCK_MAX_AGE_HOURS`: Maximum age for lock files in hours (default: 24)

#### MIME Type Detection
- `KIARINA_UTILS_MIME_HASH_ALGORITHM`: Hash algorithm for content addressing (default: "sha256")

#### Extension Detection
- `KIARINA_UTILS_EXT_MAX_MULTI_EXTENSION_PARTS`: Maximum parts for multi-extension detection (default: 4)

## Requirements

- **Python**: 3.12 or higher
- **Core dependencies**:
  - `aiofiles>=24.1.0` - Async file operations
  - `charset-normalizer>=3.4.3` - Encoding detection
  - `filelock>=3.19.1` - File locking
  - `pydantic>=2.11.7` - Data validation
  - `pydantic-settings>=2.10.1` - Settings management
  - `pydantic-settings-manager>=2.1.0` - Advanced settings management
  - `pyyaml>=6.0.2` - YAML support

- **Optional dependencies**:
  - `puremagic>=1.30` - Enhanced MIME type detection from file content

## Development

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for dependency management
- [mise](https://mise.jdx.dev/) for task running

### Setup

```bash
# Clone the repository
git clone https://github.com/kiarina/kiarina-python.git
cd kiarina-python

# Setup development environment
mise run setup

# Install dependencies for this package
cd packages/kiarina-utils-file
uv sync --group dev
```

### Running Tests

```bash
# Run all tests
mise run package:test kiarina-utils-file

# Run with coverage
mise run package:test kiarina-utils-file --coverage

# Run specific test files
uv run --group test pytest tests/file/test_kiarina_utils_file_sync.py
uv run --group test pytest tests/file/test_kiarina_utils_file_async.py
```

### Code Quality

```bash
# Format code
mise run package:format kiarina-utils-file

# Run linting
mise run package:lint kiarina-utils-file

# Type checking
mise run package:typecheck kiarina-utils-file

# Run all checks
mise run package kiarina-utils-file
```

## Performance

### Benchmarks

The library is optimized for performance with several key features:

- **Lazy loading**: Properties are computed only when accessed
- **Caching**: Expensive operations like encoding detection are cached
- **Async support**: Non-blocking I/O for high-throughput applications
- **Efficient sampling**: Large files are sampled for encoding/MIME detection
- **Atomic operations**: Safe concurrent file access with minimal overhead

### Memory Usage

- **Streaming support**: Large files can be processed without loading entirely into memory
- **Configurable sampling**: Detection algorithms use configurable sample sizes
- **Efficient caching**: Only frequently accessed properties are cached

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Contributing

This is a personal project, but contributions are welcome! Please feel free to submit issues or pull requests.

### Guidelines

1. **Code Style**: Follow the existing code style (enforced by ruff)
2. **Testing**: Add tests for new functionality
3. **Documentation**: Update documentation for API changes
4. **Type Hints**: Maintain full type hint coverage

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - The main monorepo containing this package
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Configuration management library used by this package

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## Support

- **Issues**: [GitHub Issues](https://github.com/kiarina/kiarina-python/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kiarina/kiarina-python/discussions)

---

Made with ❤️ by [kiarina](https://github.com/kiarina)
