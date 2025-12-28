"""Checksum calculation and verification for dossier body content."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any

import frontmatter as fm

from .parser import ParsedDossier, parse_content


class ChecksumStatus(Enum):
    """Status of checksum verification."""

    VALID = "valid"  # Checksum matches
    INVALID = "invalid"  # Checksum doesn't match
    MISSING = "missing"  # No checksum in frontmatter


@dataclass
class ChecksumResult:
    """Result of checksum verification."""

    status: ChecksumStatus
    expected: str | None = None  # From frontmatter
    actual: str | None = None  # Calculated from body

    @property
    def valid(self) -> bool:
        """Return True if checksum is valid."""
        return self.status == ChecksumStatus.VALID


def calculate_checksum(body: str) -> str:
    """Calculate SHA256 checksum of body content.

    Args:
        body: The body content (after frontmatter)

    Returns:
        Lowercase hex SHA256 hash (64 characters)
    """
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def verify_checksum(body: str, frontmatter: dict[str, Any]) -> ChecksumResult:
    """Verify body checksum against frontmatter.

    Args:
        body: The body content
        frontmatter: Frontmatter dict (expects checksum.hash)

    Returns:
        ChecksumResult with status and hash values
    """
    checksum_obj = frontmatter.get("checksum")
    if not checksum_obj or "hash" not in checksum_obj:
        return ChecksumResult(status=ChecksumStatus.MISSING)

    expected = checksum_obj["hash"]
    actual = calculate_checksum(body)

    if expected == actual:
        return ChecksumResult(
            status=ChecksumStatus.VALID,
            expected=expected,
            actual=actual,
        )
    return ChecksumResult(
        status=ChecksumStatus.INVALID,
        expected=expected,
        actual=actual,
    )


def verify_dossier_checksum(parsed: ParsedDossier) -> ChecksumResult:
    """Verify checksum of a parsed dossier.

    Args:
        parsed: ParsedDossier from parser module

    Returns:
        ChecksumResult with status and hash values
    """
    return verify_checksum(parsed.body, parsed.frontmatter)


def update_checksum(content: str) -> str:
    """Parse content, recalculate checksum, return updated content.

    Args:
        content: Raw .ds.md file content

    Returns:
        Content with updated checksum in frontmatter

    Raises:
        ParseError: If content cannot be parsed
    """
    parsed = parse_content(content)
    new_hash = calculate_checksum(parsed.body)

    # Update frontmatter
    parsed.frontmatter.setdefault("checksum", {})
    parsed.frontmatter["checksum"]["algorithm"] = "sha256"
    parsed.frontmatter["checksum"]["hash"] = new_hash

    # Reconstruct file
    post = fm.Post(parsed.body, **parsed.frontmatter)
    return fm.dumps(post)
