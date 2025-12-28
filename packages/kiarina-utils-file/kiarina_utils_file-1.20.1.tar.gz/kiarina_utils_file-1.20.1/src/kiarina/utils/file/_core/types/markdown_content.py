from typing import Any, NamedTuple


class MarkdownContent(NamedTuple):
    """
    Markdown content with optional YAML front matter metadata.

    This class represents the result of parsing a Markdown file that may contain
    YAML front matter. The front matter is extracted and parsed into metadata,
    while the remaining content is stored separately.

    Attributes:
        content (str): Markdown content without the YAML front matter block.
            If the file has no front matter, this contains the entire file content.
        metadata (dict[str, Any]): Parsed YAML front matter as a dictionary.
            If the file has no front matter or the front matter is invalid,
            this is an empty dictionary.

    Examples:
        >>> # File with front matter:
        >>> # ---
        >>> # title: Example
        >>> # author: John Doe
        >>> # ---
        >>> # # Content
        >>> result = MarkdownContent(
        ...     content="# Content\\n",
        ...     metadata={"title": "Example", "author": "John Doe"}
        ... )
        >>> print(result.content)
        # Content
        >>> print(result.metadata["title"])
        Example

        >>> # File without front matter:
        >>> result = MarkdownContent(
        ...     content="# Just Content\\n",
        ...     metadata={}
        ... )
        >>> print(result.content)
        # Just Content
        >>> print(result.metadata)
        {}
    """

    content: str
    """Markdown content (without front matter)"""

    metadata: dict[str, Any]
    """YAML front matter metadata (empty dict if no front matter)"""
