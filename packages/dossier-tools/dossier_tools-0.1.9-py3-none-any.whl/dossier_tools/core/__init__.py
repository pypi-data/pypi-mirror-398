"""Core dossier parsing, validation, and checksum functionality."""

from .checksum import (
    ChecksumResult,
    ChecksumStatus,
    calculate_checksum,
    update_checksum,
    verify_checksum,
    verify_dossier_checksum,
)
from .parser import ParsedDossier, ParseError, parse_content, parse_file
from .validate import (
    ValidationResult,
    get_schema_path,
    load_schema,
    validate_content,
    validate_file,
    validate_frontmatter,
)

__all__ = [
    # checksum
    "ChecksumResult",
    "ChecksumStatus",
    "ParseError",
    # parser
    "ParsedDossier",
    # validate
    "ValidationResult",
    "calculate_checksum",
    "get_schema_path",
    "load_schema",
    "parse_content",
    "parse_file",
    "update_checksum",
    "validate_content",
    "validate_file",
    "validate_frontmatter",
    "verify_checksum",
    "verify_dossier_checksum",
]
