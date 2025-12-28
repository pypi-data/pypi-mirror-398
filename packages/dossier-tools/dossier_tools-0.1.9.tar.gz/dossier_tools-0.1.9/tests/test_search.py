"""Tests for search functionality."""

import json

import respx
from click.testing import CliRunner
from httpx import Response

from dossier_tools.cli import main
from dossier_tools.search import (
    SearchMatch,
    SearchResult,
    search_content,
    search_metadata,
)


class TestSearchMetadata:
    """Tests for search_metadata."""

    def test_matches_name(self):
        """Should match in name field."""
        dossier = {"name": "myorg/react-setup", "title": "Setup", "description": None}
        matches = search_metadata(dossier, "react")

        assert len(matches) == 1
        assert matches[0].field == "name"

    def test_matches_title(self):
        """Should match in title field."""
        dossier = {"name": "myorg/setup", "title": "React Setup Guide"}
        matches = search_metadata(dossier, "react")

        assert len(matches) == 1
        assert matches[0].field == "title"

    def test_matches_description(self):
        """Should match in description field."""
        dossier = {"name": "myorg/setup", "title": "Setup", "description": "Setup a React project"}
        matches = search_metadata(dossier, "react")

        assert len(matches) == 1
        assert matches[0].field == "description"

    def test_matches_tags(self):
        """Should match in tags list."""
        dossier = {"name": "myorg/setup", "title": "Setup", "tags": ["react", "frontend"]}
        matches = search_metadata(dossier, "frontend")

        assert len(matches) == 1
        assert matches[0].field == "tags"

    def test_matches_category(self):
        """Should match in category list."""
        dossier = {"name": "myorg/setup", "title": "Setup", "category": ["development"]}
        matches = search_metadata(dossier, "development")

        assert len(matches) == 1
        assert matches[0].field == "category"

    def test_case_insensitive(self):
        """Should match case-insensitively."""
        dossier = {"name": "myorg/REACT-setup", "title": "Setup"}
        matches = search_metadata(dossier, "react")

        assert len(matches) == 1

    def test_no_match(self):
        """Should return empty list when no match."""
        dossier = {"name": "myorg/vue-setup", "title": "Vue Setup"}
        matches = search_metadata(dossier, "react")

        assert len(matches) == 0

    def test_multiple_matches(self):
        """Should return all matching fields."""
        dossier = {
            "name": "myorg/react-setup",
            "title": "React Setup Guide",
            "tags": ["react", "frontend"],
        }
        matches = search_metadata(dossier, "react")

        assert len(matches) == 3
        fields = {m.field for m in matches}
        assert fields == {"name", "title", "tags"}

    def test_partial_match_in_tags(self):
        """Should match partial strings in tags."""
        dossier = {"name": "myorg/setup", "title": "Setup", "tags": ["react-native", "mobile"]}
        matches = search_metadata(dossier, "react")

        assert len(matches) == 1
        assert matches[0].field == "tags"


class TestSearchContent:
    """Tests for search_content."""

    def test_matches_content(self):
        """Should find match in content."""
        content = "This is a guide for setting up React projects."
        match = search_content(content, "React")

        assert match is not None
        assert match.field == "content"
        assert "React" in match.context

    def test_case_insensitive(self):
        """Should match case-insensitively."""
        content = "This is about REACT."
        match = search_content(content, "react")

        assert match is not None

    def test_no_match(self):
        """Should return None when no match."""
        content = "This is about Vue."
        match = search_content(content, "react")

        assert match is None

    def test_context_snippet(self):
        """Should include context around match."""
        content = "A" * 100 + " React " + "B" * 100
        match = search_content(content, "React")

        assert match is not None
        assert "React" in match.context
        assert len(match.context) < len(content)

    def test_context_ellipsis_start(self):
        """Should add ellipsis at start when trimmed."""
        content = "A" * 100 + "React"
        match = search_content(content, "React")

        assert match is not None
        assert match.context.startswith("...")

    def test_context_ellipsis_end(self):
        """Should add ellipsis at end when trimmed."""
        content = "React" + "B" * 100
        match = search_content(content, "React")

        assert match is not None
        assert match.context.endswith("...")

    def test_short_content_no_ellipsis(self):
        """Should not add ellipsis for short content."""
        content = "React is great"
        match = search_content(content, "React")

        assert match is not None
        assert not match.context.startswith("...")
        assert not match.context.endswith("...")


class TestSearchResult:
    """Tests for SearchResult."""

    def test_match_type_metadata(self):
        """Should return 'metadata' when no content matches."""
        result = SearchResult(
            name="test",
            title="Test",
            version="1.0.0",
            description=None,
            category=[],
            tags=[],
            matches=[SearchMatch(field="name")],
        )

        assert result.match_type == "metadata"

    def test_match_type_content(self):
        """Should return 'content' when content match exists."""
        result = SearchResult(
            name="test",
            title="Test",
            version="1.0.0",
            description=None,
            category=[],
            tags=[],
            matches=[SearchMatch(field="content", context="...")],
        )

        assert result.match_type == "content"

    def test_match_type_mixed(self):
        """Should return 'content' when both metadata and content matches exist."""
        result = SearchResult(
            name="test",
            title="Test",
            version="1.0.0",
            description=None,
            category=[],
            tags=[],
            matches=[
                SearchMatch(field="name"),
                SearchMatch(field="content", context="..."),
            ],
        )

        assert result.match_type == "content"

    def test_to_dict(self):
        """Should convert to dict."""
        result = SearchResult(
            name="test",
            title="Test",
            version="1.0.0",
            description="A test",
            category=["dev"],
            tags=["test"],
            matches=[SearchMatch(field="name")],
        )

        d = result.to_dict()

        assert d["name"] == "test"
        assert d["title"] == "Test"
        assert d["version"] == "1.0.0"
        assert d["description"] == "A test"
        assert d["category"] == ["dev"]
        assert d["tags"] == ["test"]
        assert d["match_type"] == "metadata"
        assert len(d["matches"]) == 1
        assert d["matches"][0]["field"] == "name"


class TestSearchCLI:
    """Tests for search CLI command."""

    @respx.mock
    def test_search_no_results(self, monkeypatch):
        """Should show message when no results found."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                200,
                json={"dossiers": [], "pagination": {"page": 1, "per_page": 100, "total": 0}},
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["search", "nonexistent"])

        assert result.exit_code == 0
        assert "No dossiers found" in result.output

    @respx.mock
    def test_search_metadata_match(self, monkeypatch):
        """Should find dossiers matching metadata."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                200,
                json={
                    "dossiers": [
                        {"name": "myorg/react-setup", "title": "React Setup", "version": "1.0.0", "tags": ["react"]},
                        {"name": "myorg/vue-setup", "title": "Vue Setup", "version": "1.0.0", "tags": ["vue"]},
                    ],
                    "pagination": {"page": 1, "per_page": 100, "total": 2},
                },
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["search", "react"])

        assert result.exit_code == 0
        assert "myorg/react-setup" in result.output
        assert "myorg/vue-setup" not in result.output

    @respx.mock
    def test_search_json_output(self, monkeypatch):
        """Should output JSON with --json."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                200,
                json={
                    "dossiers": [
                        {"name": "myorg/react-setup", "title": "React", "version": "1.0.0"},
                    ],
                    "pagination": {"page": 1, "per_page": 100, "total": 1},
                },
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["search", "react", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["name"] == "myorg/react-setup"

    @respx.mock
    def test_search_with_limit(self, monkeypatch):
        """Should respect --limit option."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                200,
                json={
                    "dossiers": [
                        {"name": f"myorg/react-{i}", "title": f"React {i}", "version": "1.0.0"} for i in range(5)
                    ],
                    "pagination": {"page": 1, "per_page": 100, "total": 5},
                },
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["search", "react", "--limit", "2", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2

    @respx.mock
    def test_search_registry_error(self, monkeypatch):
        """Should show error on registry failure."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(500, json={"error": {"message": "Server error"}})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["search", "react"])

        assert result.exit_code == 1
        assert "Error" in result.output

    @respx.mock
    def test_search_shows_tags(self, monkeypatch):
        """Should display tags in output."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                200,
                json={
                    "dossiers": [
                        {
                            "name": "myorg/react-setup",
                            "title": "React Setup",
                            "version": "1.0.0",
                            "tags": ["react", "frontend"],
                        },
                    ],
                    "pagination": {"page": 1, "per_page": 100, "total": 1},
                },
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["search", "react"])

        assert result.exit_code == 0
        assert "[react, frontend]" in result.output

    @respx.mock
    def test_search_pagination(self, monkeypatch):
        """Should fetch all pages when paginated."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        # First page
        respx.get("https://registry.test/api/v1/dossiers").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "dossiers": [
                            {"name": "myorg/react-1", "title": "React 1", "version": "1.0.0"},
                        ],
                        "pagination": {"page": 1, "per_page": 1, "total": 2},
                    },
                ),
                Response(
                    200,
                    json={
                        "dossiers": [
                            {"name": "myorg/react-2", "title": "React 2", "version": "1.0.0"},
                        ],
                        "pagination": {"page": 2, "per_page": 1, "total": 2},
                    },
                ),
            ]
        )

        runner = CliRunner()
        result = runner.invoke(main, ["search", "react", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2
