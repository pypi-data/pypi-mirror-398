"""Tests for the validate module."""

from dossier_tools.core import (
    load_schema,
    validate_content,
    validate_file,
    validate_frontmatter,
)

from .conftest import FIXTURES_DIR


class TestLoadSchema:
    """Tests for load_schema function."""

    def test_load_default_schema(self):
        """Should load the bundled schema."""
        schema = load_schema()

        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert "schema_version" in schema["required"]
        assert "checksum" in schema["required"]

    def test_load_custom_schema(self, tmp_path):
        """Should load schema from custom path."""
        schema_file = tmp_path / "custom.json"
        schema_file.write_text('{"type": "object", "required": ["foo"]}')

        schema = load_schema(schema_file)
        assert schema["required"] == ["foo"]


class TestValidateFrontmatter:
    """Tests for validate_frontmatter function."""

    def test_valid_minimal_frontmatter(self):
        """Should validate minimal valid frontmatter."""
        frontmatter = {
            "schema_version": "1.0.0",
            "name": "test-dossier",
            "title": "Test Dossier",
            "version": "1.0.0",
            "status": "stable",
            "objective": "A test dossier for validation testing",
            "checksum": {"algorithm": "sha256", "hash": "a" * 64},
            "authors": [{"name": "Test Author"}],
        }

        result = validate_frontmatter(frontmatter)

        assert result.valid is True
        assert result.errors == []
        assert result.frontmatter == frontmatter

    def test_missing_required_field(self):
        """Should fail when required field is missing."""
        frontmatter = {
            "schema_version": "1.0.0",
            "name": "test-dossier",
            # missing title
            "version": "1.0.0",
            "status": "stable",
            "objective": "A test dossier for validation testing",
            "checksum": {"algorithm": "sha256", "hash": "a" * 64},
            "authors": [{"name": "Test Author"}],
        }

        result = validate_frontmatter(frontmatter)

        assert result.valid is False
        assert any("title" in err for err in result.errors)

    def test_invalid_status_enum(self):
        """Should fail for invalid status enum value."""
        frontmatter = {
            "schema_version": "1.0.0",
            "name": "test-dossier",
            "title": "Test",
            "version": "1.0.0",
            "status": "invalid_status",
            "objective": "A test dossier for validation testing",
            "checksum": {"algorithm": "sha256", "hash": "a" * 64},
            "authors": [{"name": "Test Author"}],
        }

        result = validate_frontmatter(frontmatter)

        assert result.valid is False
        assert any("status" in err.lower() or "invalid_status" in err for err in result.errors)

    def test_invalid_version_format(self):
        """Should fail for invalid version format."""
        frontmatter = {
            "schema_version": "1.0.0",
            "name": "test-dossier",
            "title": "Test",
            "version": "not-semver",
            "status": "stable",
            "objective": "A test dossier for validation testing",
            "checksum": {"algorithm": "sha256", "hash": "a" * 64},
            "authors": [{"name": "Test Author"}],
        }

        result = validate_frontmatter(frontmatter)

        assert result.valid is False

    def test_missing_checksum(self):
        """Should fail when checksum is missing."""
        frontmatter = {
            "schema_version": "1.0.0",
            "name": "test-dossier",
            "title": "Test",
            "version": "1.0.0",
            "status": "stable",
            "objective": "A test dossier for validation testing",
            "authors": [{"name": "Test Author"}],
            # missing checksum
        }

        result = validate_frontmatter(frontmatter)

        assert result.valid is False
        assert any("checksum" in err for err in result.errors)

    def test_invalid_checksum_hash_format(self):
        """Should fail for invalid checksum hash format."""
        frontmatter = {
            "schema_version": "1.0.0",
            "name": "test-dossier",
            "title": "Test",
            "version": "1.0.0",
            "status": "stable",
            "objective": "A test dossier for validation testing",
            "checksum": {"algorithm": "sha256", "hash": "not-a-valid-hash"},
            "authors": [{"name": "Test Author"}],
        }

        result = validate_frontmatter(frontmatter)

        assert result.valid is False


class TestValidateFile:
    """Tests for validate_file function."""

    def test_validate_valid_minimal_file(self):
        """Should validate a valid minimal dossier file."""
        path = FIXTURES_DIR / "valid" / "minimal.ds.md"
        result = validate_file(path)

        assert result.valid is True
        assert result.errors == []

    def test_validate_valid_full_file(self):
        """Should validate a valid full dossier file."""
        path = FIXTURES_DIR / "valid" / "full.ds.md"
        result = validate_file(path)

        assert result.valid is True

    def test_validate_missing_title_file(self):
        """Should fail for file missing required title."""
        path = FIXTURES_DIR / "invalid" / "missing-title.ds.md"
        result = validate_file(path)

        assert result.valid is False
        assert any("title" in err for err in result.errors)

    def test_validate_missing_checksum_file(self):
        """Should fail for file missing required checksum."""
        path = FIXTURES_DIR / "invalid" / "missing-checksum.ds.md"
        result = validate_file(path)

        assert result.valid is False
        assert any("checksum" in err for err in result.errors)

    def test_validate_bad_status_file(self):
        """Should fail for file with invalid status."""
        path = FIXTURES_DIR / "invalid" / "bad-status.ds.md"
        result = validate_file(path)

        assert result.valid is False

    def test_validate_bad_version_file(self):
        """Should fail for file with invalid version."""
        path = FIXTURES_DIR / "invalid" / "bad-version.ds.md"
        result = validate_file(path)

        assert result.valid is False

    def test_validate_nonexistent_file(self):
        """Should fail for nonexistent file."""
        path = FIXTURES_DIR / "nonexistent.ds.md"
        result = validate_file(path)

        assert result.valid is False
        assert any("not found" in err.lower() for err in result.errors)

    def test_validate_no_frontmatter_file(self):
        """Should fail for file without frontmatter."""
        path = FIXTURES_DIR / "invalid" / "no-frontmatter.ds.md"
        result = validate_file(path)

        assert result.valid is False
        assert any("frontmatter" in err.lower() for err in result.errors)


class TestValidateContent:
    """Tests for validate_content function."""

    def test_validate_valid_content(self):
        """Should validate valid content string."""
        content = """---
schema_version: "1.0.0"
name: "test-dossier"
title: "Test"
version: "1.0.0"
status: "stable"
objective: "A test dossier for content validation"
checksum:
  algorithm: "sha256"
  hash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
authors:
  - name: "Test Author"
---

Body content.
"""
        result = validate_content(content)

        assert result.valid is True

    def test_validate_invalid_content(self):
        """Should fail for invalid content."""
        content = """---
schema_version: "1.0.0"
title: "Test"
---

Missing required fields.
"""
        result = validate_content(content)

        assert result.valid is False
