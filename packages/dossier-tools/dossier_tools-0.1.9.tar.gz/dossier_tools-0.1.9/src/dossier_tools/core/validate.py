"""Validate dossier frontmatter against JSON schema."""

import json
from dataclasses import dataclass, field
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

from .parser import ParseError, parse_content, parse_file


@dataclass
class ValidationResult:
    """Result of schema validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    frontmatter: dict[str, Any] | None = None


def get_schema_path() -> Path:
    """Get path to bundled schema file.

    Note: Prefer load_schema() which uses importlib.resources for installed packages.
    This function is kept for backward compatibility and testing.
    """
    return Path(__file__).parent.parent.parent.parent / "schema" / "dossier-schema.json"


@lru_cache(maxsize=1)
def _load_default_schema() -> dict[str, Any]:
    """Load and cache the default schema."""
    # Try loading from package resources first (works when installed via pip)
    try:
        schema_file = resources.files("dossier_tools") / "schema" / "dossier-schema.json"
        return json.loads(schema_file.read_text())
    except (TypeError, FileNotFoundError):
        # Fall back to filesystem path (development mode)
        return json.loads(get_schema_path().read_text())


def load_schema(path: Path | None = None) -> dict[str, Any]:
    """Load JSON schema from file or package resources.

    Args:
        path: Path to schema file. If not provided, loads cached default schema.

    Returns:
        Schema as dictionary
    """
    if path is not None:
        return json.loads(path.read_text())

    return _load_default_schema()


def validate_frontmatter(
    frontmatter: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> ValidationResult:
    """Validate frontmatter dict against schema.

    Args:
        frontmatter: The frontmatter dictionary to validate
        schema: Optional schema dict (loads default if not provided)

    Returns:
        ValidationResult with valid flag and any errors
    """
    if schema is None:
        schema = load_schema()

    errors: list[str] = []
    try:
        validate(instance=frontmatter, schema=schema)
    except ValidationError as e:
        errors.append(e.message)
        if e.path:
            errors.append(f"  at: {'.'.join(str(p) for p in e.path)}")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        frontmatter=frontmatter,
    )


def validate_file(
    path: Path | str,
    schema: dict[str, Any] | None = None,
) -> ValidationResult:
    """Parse and validate a .ds.md file.

    Args:
        path: Path to the .ds.md file
        schema: Optional schema dict

    Returns:
        ValidationResult with valid flag and any errors
    """
    try:
        parsed = parse_file(path)
    except ParseError as e:
        return ValidationResult(valid=False, errors=[str(e)])

    return validate_frontmatter(parsed.frontmatter, schema)


def validate_content(
    content: str,
    schema: dict[str, Any] | None = None,
) -> ValidationResult:
    """Parse and validate raw .ds.md content.

    Args:
        content: Raw file content
        schema: Optional schema dict

    Returns:
        ValidationResult with valid flag and any errors
    """
    try:
        parsed = parse_content(content)
    except ParseError as e:
        return ValidationResult(valid=False, errors=[str(e)])

    return validate_frontmatter(parsed.frontmatter, schema)
