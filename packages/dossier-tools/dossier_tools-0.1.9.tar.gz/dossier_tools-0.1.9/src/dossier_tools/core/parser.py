"""Parse .ds.md dossier files into frontmatter and body."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter


@dataclass
class ParsedDossier:
    """Result of parsing a .ds.md file."""

    frontmatter: dict[str, Any]
    body: str
    raw: str


class ParseError(Exception):
    """Raised when parsing fails."""


def parse_content(content: str) -> ParsedDossier:
    """Parse dossier content into frontmatter and body.

    Args:
        content: Raw file content with YAML/JSON frontmatter

    Returns:
        ParsedDossier with frontmatter dict and body string

    Raises:
        ParseError: If parsing fails or no frontmatter found
    """
    try:
        post = frontmatter.loads(content)
    except Exception as e:
        msg = f"Failed to parse frontmatter: {e}"
        raise ParseError(msg) from e

    if not post.metadata:
        raise ParseError("No frontmatter found")

    return ParsedDossier(
        frontmatter=post.metadata,
        body=post.content,
        raw=content,
    )


def parse_file(path: Path | str) -> ParsedDossier:
    """Parse a .ds.md file.

    Args:
        path: Path to the .ds.md file

    Returns:
        ParsedDossier with frontmatter dict and body string

    Raises:
        ParseError: If file not found or parsing fails
    """
    path = Path(path)
    if not path.exists():
        msg = f"File not found: {path}"
        raise ParseError(msg)

    content = path.read_text(encoding="utf-8")
    return parse_content(content)
