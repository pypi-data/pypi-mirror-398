"""Tests for the parser module."""

import pytest

from dossier_tools.core import ParsedDossier, ParseError, parse_content, parse_file

from .conftest import FIXTURES_DIR


class TestParseContent:
    """Tests for parse_content function."""

    def test_parse_yaml_frontmatter(self):
        """Should parse valid YAML frontmatter."""
        content = """---
title: Test
version: "1.0.0"
---

Body content here.
"""
        result = parse_content(content)

        assert isinstance(result, ParsedDossier)
        assert result.frontmatter["title"] == "Test"
        assert result.frontmatter["version"] == "1.0.0"
        assert "Body content here." in result.body
        assert result.raw == content

    def test_parse_json_frontmatter(self):
        """Should parse valid JSON frontmatter."""
        content = """---
{"title": "Test", "version": "1.0.0"}
---

Body content here.
"""
        result = parse_content(content)

        assert result.frontmatter["title"] == "Test"
        assert result.frontmatter["version"] == "1.0.0"

    def test_parse_no_frontmatter_raises(self):
        """Should raise ParseError when no frontmatter found."""
        content = "Just some text without frontmatter."

        with pytest.raises(ParseError, match="No frontmatter found"):
            parse_content(content)

    def test_parse_empty_frontmatter_raises(self):
        """Should raise ParseError when frontmatter is empty."""
        content = """---
---

Body content.
"""
        with pytest.raises(ParseError, match="No frontmatter found"):
            parse_content(content)

    def test_preserves_body_whitespace(self):
        """Should preserve body content exactly including whitespace."""
        content = """---
title: Test
---

Line 1

  Indented line

Line 4
"""
        result = parse_content(content)

        assert "Line 1" in result.body
        assert "  Indented line" in result.body
        assert "Line 4" in result.body


class TestParseFile:
    """Tests for parse_file function."""

    def test_parse_valid_minimal_file(self):
        """Should parse a valid minimal dossier file."""
        path = FIXTURES_DIR / "valid" / "minimal.ds.md"
        result = parse_file(path)

        assert result.frontmatter["schema_version"] == "1.0.0"
        assert result.frontmatter["title"] == "Minimal Dossier"
        assert result.frontmatter["status"] == "stable"
        assert "# Minimal Dossier" in result.body

    def test_parse_valid_full_file(self):
        """Should parse a valid full dossier file."""
        path = FIXTURES_DIR / "valid" / "full.ds.md"
        result = parse_file(path)

        assert result.frontmatter["title"] == "Full Featured Dossier"
        assert result.frontmatter["risk_level"] == "medium"
        assert "docker" in result.frontmatter["tags"]

    def test_parse_file_not_found(self):
        """Should raise ParseError when file not found."""
        path = FIXTURES_DIR / "nonexistent.ds.md"

        with pytest.raises(ParseError, match="File not found"):
            parse_file(path)

    def test_parse_file_accepts_string_path(self):
        """Should accept string path."""
        path = str(FIXTURES_DIR / "valid" / "minimal.ds.md")
        result = parse_file(path)

        assert result.frontmatter["title"] == "Minimal Dossier"

    def test_parse_no_frontmatter_file(self):
        """Should raise ParseError for file without frontmatter."""
        path = FIXTURES_DIR / "invalid" / "no-frontmatter.ds.md"

        with pytest.raises(ParseError, match="No frontmatter found"):
            parse_file(path)
