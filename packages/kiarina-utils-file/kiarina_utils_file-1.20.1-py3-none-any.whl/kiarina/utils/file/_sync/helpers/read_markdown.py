import os
from typing import overload

from ..._core.operations.read_markdown import read_markdown as _read_markdown
from ..._core.types.markdown_content import MarkdownContent


@overload
def read_markdown(
    file_path: str | os.PathLike[str],
) -> MarkdownContent | None: ...


@overload
def read_markdown(
    file_path: str | os.PathLike[str],
    *,
    default: MarkdownContent,
) -> MarkdownContent: ...


def read_markdown(
    file_path: str | os.PathLike[str],
    *,
    default: MarkdownContent | None = None,
) -> MarkdownContent | None:
    """
    Read Markdown file with optional YAML front matter.

    This function reads a Markdown file and extracts YAML front matter if present.
    The front matter must be at the beginning of the file, enclosed by `---` markers.

    Front matter format:
        ---
        key1: value1
        key2: value2
        ---
        Markdown content starts here...

    Args:
        file_path (str | os.PathLike[str]): Path to the Markdown file to read
        default (MarkdownContent | None): Default value to return if file doesn't exist.
            Default is None.

    Returns:
        MarkdownContent | None:
            - MarkdownContent with content and metadata if file exists
            - default if file doesn't exist

    Examples:
        >>> import kiarina.utils.file as kf
        >>>
        >>> # Basic usage
        >>> result = kf.read_markdown("document.md")
        >>> if result:
        ...     print(f"Title: {result.metadata.get('title', 'Untitled')}")
        ...     print(f"Content: {result.content}")

        >>> # With default value
        >>> result = kf.read_markdown(
        ...     "missing.md",
        ...     default=kf.MarkdownContent(content="", metadata={})
        ... )
        >>> print(result.content)  # Always str (empty if file missing)

        >>> # Accessing metadata
        >>> result = kf.read_markdown("blog_post.md")
        >>> if result:
        ...     title = result.metadata.get("title", "Untitled")
        ...     author = result.metadata.get("author", "Unknown")
        ...     date = result.metadata.get("date")
        ...     print(f"{title} by {author}")
        ...     if date:
        ...         print(f"Published: {date}")

    Note:
        - If the file has no front matter, metadata will be an empty dict
        - If the front matter is invalid YAML, it will be treated as regular content
        - The content does not include the front matter block
        - For async operations, use `kiarina.utils.file.asyncio.read_markdown()`
    """
    return _read_markdown("sync", file_path, default=default)
