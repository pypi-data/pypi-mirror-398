"""Tests for the checksum module."""

from dossier_tools.core import (
    ChecksumResult,
    ChecksumStatus,
    calculate_checksum,
    parse_content,
    update_checksum,
    verify_checksum,
    verify_dossier_checksum,
)

# SHA256 produces 64-character hex strings
SHA256_HEX_LENGTH = 64


class TestCalculateChecksum:
    """Tests for calculate_checksum function."""

    def test_returns_64_char_hex(self):
        """Should return 64-character lowercase hex string."""
        result = calculate_checksum("test content")

        assert len(result) == SHA256_HEX_LENGTH
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        """Should return same hash for same input."""
        content = "some test content"

        result1 = calculate_checksum(content)
        result2 = calculate_checksum(content)

        assert result1 == result2

    def test_different_content_different_hash(self):
        """Should return different hashes for different content."""
        result1 = calculate_checksum("content a")
        result2 = calculate_checksum("content b")

        assert result1 != result2

    def test_empty_body(self):
        """Should handle empty body."""
        result = calculate_checksum("")

        assert len(result) == SHA256_HEX_LENGTH
        # SHA256 of empty string is well-known
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_unicode_content(self):
        """Should handle unicode content."""
        result = calculate_checksum("Hello \u4e16\u754c \U0001f600")

        assert len(result) == SHA256_HEX_LENGTH

    def test_whitespace_matters(self):
        """Should produce different hashes for different whitespace."""
        result1 = calculate_checksum("hello")
        result2 = calculate_checksum("hello ")
        result3 = calculate_checksum("hello\n")

        assert result1 != result2
        assert result1 != result3
        assert result2 != result3


class TestVerifyChecksum:
    """Tests for verify_checksum function."""

    def test_valid_checksum(self):
        """Should return VALID when checksums match."""
        body = "test body content"
        expected_hash = calculate_checksum(body)
        frontmatter = {"checksum": {"algorithm": "sha256", "hash": expected_hash}}

        result = verify_checksum(body, frontmatter)

        assert result.status == ChecksumStatus.VALID
        assert result.valid is True
        assert result.expected == expected_hash
        assert result.actual == expected_hash

    def test_invalid_checksum(self):
        """Should return INVALID when checksums don't match."""
        body = "test body content"
        frontmatter = {"checksum": {"algorithm": "sha256", "hash": "a" * 64}}

        result = verify_checksum(body, frontmatter)

        assert result.status == ChecksumStatus.INVALID
        assert result.valid is False
        assert result.expected == "a" * 64
        assert result.actual == calculate_checksum(body)

    def test_missing_checksum_field(self):
        """Should return MISSING when checksum field is absent."""
        body = "test body content"
        frontmatter = {"title": "Test"}

        result = verify_checksum(body, frontmatter)

        assert result.status == ChecksumStatus.MISSING
        assert result.valid is False
        assert result.expected is None
        assert result.actual is None

    def test_missing_hash_in_checksum(self):
        """Should return MISSING when hash is absent from checksum object."""
        body = "test body content"
        frontmatter = {"checksum": {"algorithm": "sha256"}}

        result = verify_checksum(body, frontmatter)

        assert result.status == ChecksumStatus.MISSING

    def test_empty_checksum_object(self):
        """Should return MISSING when checksum object is empty."""
        body = "test body content"
        frontmatter = {"checksum": {}}

        result = verify_checksum(body, frontmatter)

        assert result.status == ChecksumStatus.MISSING


class TestVerifyDossierChecksum:
    """Tests for verify_dossier_checksum function."""

    def test_with_parsed_dossier(self):
        """Should work with ParsedDossier object."""
        body = "# Test Body\n\nSome content.\n"
        checksum = calculate_checksum(body)
        content = f"""---
title: Test
checksum:
  algorithm: sha256
  hash: {checksum}
---

{body.rstrip()}
"""
        # Note: frontmatter library strips leading/trailing whitespace from body
        # so we need to recalculate for what parse_content will return
        parsed = parse_content(content)
        actual_checksum = calculate_checksum(parsed.body)

        # Update the content with correct checksum
        content = f"""---
title: Test
checksum:
  algorithm: sha256
  hash: {actual_checksum}
---

{body.rstrip()}
"""
        parsed = parse_content(content)
        result = verify_dossier_checksum(parsed)

        assert result.valid is True


class TestUpdateChecksum:
    """Tests for update_checksum function."""

    def test_updates_existing_checksum(self):
        """Should update existing checksum with correct value."""
        content = """---
title: Test
checksum:
  algorithm: sha256
  hash: wronghashwronghashwronghashwronghashwronghashwronghashwronghash
---

Body content here.
"""
        result = update_checksum(content)
        parsed = parse_content(result)

        # Verify the checksum is now correct
        verify_result = verify_dossier_checksum(parsed)
        assert verify_result.valid is True

    def test_adds_checksum_when_missing(self):
        """Should add checksum when not present."""
        content = """---
title: Test
---

Body content here.
"""
        result = update_checksum(content)
        parsed = parse_content(result)

        assert "checksum" in parsed.frontmatter
        assert parsed.frontmatter["checksum"]["algorithm"] == "sha256"
        assert len(parsed.frontmatter["checksum"]["hash"]) == SHA256_HEX_LENGTH

        # Verify it's correct
        verify_result = verify_dossier_checksum(parsed)
        assert verify_result.valid is True

    def test_preserves_other_frontmatter(self):
        """Should preserve other frontmatter fields."""
        content = """---
title: My Title
version: "1.0.0"
status: stable
tags:
  - foo
  - bar
---

Body content.
"""
        result = update_checksum(content)
        parsed = parse_content(result)

        assert parsed.frontmatter["title"] == "My Title"
        assert parsed.frontmatter["version"] == "1.0.0"
        assert parsed.frontmatter["status"] == "stable"
        assert parsed.frontmatter["tags"] == ["foo", "bar"]


class TestChecksumResult:
    """Tests for ChecksumResult dataclass."""

    def test_valid_property_true(self):
        """Should return True when status is VALID."""
        result = ChecksumResult(status=ChecksumStatus.VALID)
        assert result.valid is True

    def test_valid_property_false_invalid(self):
        """Should return False when status is INVALID."""
        result = ChecksumResult(status=ChecksumStatus.INVALID)
        assert result.valid is False

    def test_valid_property_false_missing(self):
        """Should return False when status is MISSING."""
        result = ChecksumResult(status=ChecksumStatus.MISSING)
        assert result.valid is False
