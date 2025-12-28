"""Tests for the registry client."""

import http
import json

import pytest
import respx
from httpx import Response

from dossier_tools.registry import (
    RegistryClient,
    RegistryError,
    get_client,
    get_registry_url,
    parse_name_version,
)


class TestRegistryClient:
    """Tests for RegistryClient."""

    @respx.mock
    def test_list_dossiers(self):
        """Should return list of dossiers."""
        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                200,
                json={
                    "dossiers": [
                        {"name": "myorg/deploy", "title": "Deploy", "version": "1.0.0"},
                        {"name": "myorg/backup", "title": "Backup", "version": "2.0.0"},
                    ],
                    "pagination": {"page": 1, "per_page": 20, "total": 2},
                },
            )
        )

        client = RegistryClient("https://registry.test")
        result = client.list_dossiers()

        assert len(result["dossiers"]) == 2
        assert result["dossiers"][0]["name"] == "myorg/deploy"
        assert result["pagination"]["total"] == 2

    @respx.mock
    def test_list_dossiers_with_category(self):
        """Should filter by category."""
        route = respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                200,
                json={"dossiers": [], "pagination": {"page": 1, "per_page": 20, "total": 0}},
            )
        )

        client = RegistryClient("https://registry.test")
        client.list_dossiers(category="devops")

        assert route.calls[0].request.url.params["category"] == "devops"

    @respx.mock
    def test_get_dossier(self):
        """Should return dossier metadata."""
        respx.get("https://registry.test/api/v1/dossiers/myorg/deploy").mock(
            return_value=Response(
                200,
                json={
                    "name": "myorg/deploy",
                    "title": "Deploy to Production",
                    "version": "1.2.0",
                    "status": "stable",
                    "objective": "Deploy the application",
                },
            )
        )

        client = RegistryClient("https://registry.test")
        result = client.get_dossier("myorg/deploy")

        assert result["name"] == "myorg/deploy"
        assert result["version"] == "1.2.0"

    @respx.mock
    def test_get_dossier_with_version(self):
        """Should request specific version."""
        route = respx.get("https://registry.test/api/v1/dossiers/myorg/deploy").mock(
            return_value=Response(200, json={"name": "myorg/deploy", "version": "1.0.0"})
        )

        client = RegistryClient("https://registry.test")
        client.get_dossier("myorg/deploy", version="1.0.0")

        assert route.calls[0].request.url.params["version"] == "1.0.0"

    @respx.mock
    def test_get_dossier_not_found(self):
        """Should raise RegistryError on 404."""
        respx.get("https://registry.test/api/v1/dossiers/myorg/missing").mock(
            return_value=Response(
                404,
                json={"error": {"code": "DOSSIER_NOT_FOUND", "message": "Dossier not found"}},
            )
        )

        client = RegistryClient("https://registry.test")

        with pytest.raises(RegistryError) as exc_info:
            client.get_dossier("myorg/missing")

        assert exc_info.value.status_code == http.HTTPStatus.NOT_FOUND
        assert exc_info.value.code == "DOSSIER_NOT_FOUND"
        assert "not found" in str(exc_info.value)

    @respx.mock
    def test_pull_content(self):
        """Should return content and digest."""
        content = """---
title: Deploy
version: "1.0.0"
---

# Deploy
"""
        respx.get("https://registry.test/api/v1/dossiers/myorg/deploy/content").mock(
            return_value=Response(
                200,
                text=content,
                headers={"X-Dossier-Digest": "sha256:abc123"},
            )
        )

        client = RegistryClient("https://registry.test")
        result_content, digest = client.pull_content("myorg/deploy")

        assert result_content == content
        assert digest == "sha256:abc123"

    @respx.mock
    def test_pull_content_with_version(self):
        """Should request specific version."""
        route = respx.get("https://registry.test/api/v1/dossiers/myorg/deploy/content").mock(
            return_value=Response(200, text="content", headers={})
        )

        client = RegistryClient("https://registry.test")
        client.pull_content("myorg/deploy", version="1.0.0")

        assert route.calls[0].request.url.params["version"] == "1.0.0"

    @respx.mock
    def test_pull_content_not_found(self):
        """Should raise RegistryError on 404."""
        respx.get("https://registry.test/api/v1/dossiers/myorg/missing/content").mock(
            return_value=Response(
                404,
                json={"error": {"code": "DOSSIER_NOT_FOUND", "message": "Dossier not found"}},
            )
        )

        client = RegistryClient("https://registry.test")

        with pytest.raises(RegistryError) as exc_info:
            client.pull_content("myorg/missing")

        assert exc_info.value.status_code == http.HTTPStatus.NOT_FOUND

    @respx.mock
    def test_auth_header(self):
        """Should include Authorization header when token provided."""
        route = respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(200, json={"dossiers": [], "pagination": {}})
        )

        client = RegistryClient("https://registry.test", token="my-token")
        client.list_dossiers()

        assert route.calls[0].request.headers["Authorization"] == "Bearer my-token"

    @respx.mock
    def test_server_error(self):
        """Should raise RegistryError on 500."""
        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(500, json={"error": {"message": "Internal server error"}})
        )

        client = RegistryClient("https://registry.test")

        with pytest.raises(RegistryError) as exc_info:
            client.list_dossiers()

        assert exc_info.value.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR

    def test_context_manager(self):
        """Should work as context manager."""
        with RegistryClient("https://registry.test") as client:
            assert client.base_url == "https://registry.test"

    @respx.mock
    def test_exchange_code(self):
        """Should exchange code for token."""
        respx.post("https://registry.test/api/v1/auth/token").mock(
            return_value=Response(
                200,
                json={"access_token": "my-access-token", "token_type": "bearer"},
            )
        )

        client = RegistryClient("https://registry.test")
        result = client.exchange_code("auth-code", "http://localhost:8000/callback")

        assert result["access_token"] == "my-access-token"

    @respx.mock
    def test_exchange_code_invalid(self):
        """Should raise on invalid code."""
        respx.post("https://registry.test/api/v1/auth/token").mock(
            return_value=Response(
                400,
                json={"error": {"code": "INVALID_CODE", "message": "Invalid authorization code"}},
            )
        )

        client = RegistryClient("https://registry.test")

        with pytest.raises(RegistryError) as exc_info:
            client.exchange_code("bad-code", "http://localhost:8000/callback")

        assert exc_info.value.status_code == http.HTTPStatus.BAD_REQUEST
        assert exc_info.value.code == "INVALID_CODE"

    @respx.mock
    def test_get_me(self):
        """Should return user info."""
        respx.get("https://registry.test/api/v1/me").mock(
            return_value=Response(
                200,
                json={"username": "alice", "email": "alice@example.com", "name": "Alice"},
            )
        )

        client = RegistryClient("https://registry.test", token="my-token")
        result = client.get_me()

        assert result["username"] == "alice"
        assert result["email"] == "alice@example.com"

    @respx.mock
    def test_get_me_unauthorized(self):
        """Should raise on 401."""
        respx.get("https://registry.test/api/v1/me").mock(
            return_value=Response(
                401,
                json={"error": {"code": "UNAUTHORIZED", "message": "Invalid or expired token"}},
            )
        )

        client = RegistryClient("https://registry.test")

        with pytest.raises(RegistryError) as exc_info:
            client.get_me()

        assert exc_info.value.status_code == http.HTTPStatus.UNAUTHORIZED

    @respx.mock
    def test_publish(self):
        """Should publish dossier."""
        route = respx.post("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                201,
                json={
                    "name": "myorg/tools/deploy",
                    "version": "1.0.0",
                    "content_url": "https://cdn.test/myorg/tools/deploy",
                },
            )
        )

        client = RegistryClient("https://registry.test", token="my-token")
        result = client.publish("myorg/tools", "---\ntitle: Deploy\n---\n# Deploy")

        assert result["name"] == "myorg/tools/deploy"
        body = json.loads(route.calls[0].request.content)
        assert body["namespace"] == "myorg/tools"

    @respx.mock
    def test_publish_with_changelog(self):
        """Should include changelog in request."""
        route = respx.post("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(201, json={"name": "myorg/tools/deploy", "version": "1.0.0"})
        )

        client = RegistryClient("https://registry.test", token="my-token")
        client.publish("myorg/tools", "content", changelog="Fixed bug")

        body = json.loads(route.calls[0].request.content)
        assert body["namespace"] == "myorg/tools"
        assert body["changelog"] == "Fixed bug"

    @respx.mock
    def test_publish_unauthorized(self):
        """Should raise on 401."""
        respx.post("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                401,
                json={"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}},
            )
        )

        client = RegistryClient("https://registry.test")

        with pytest.raises(RegistryError) as exc_info:
            client.publish("myorg/tools", "content")

        assert exc_info.value.status_code == http.HTTPStatus.UNAUTHORIZED

    @respx.mock
    def test_publish_conflict(self):
        """Should raise on 409 version conflict."""
        respx.post("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                409,
                json={"error": {"code": "VERSION_EXISTS", "message": "Version 1.0.0 already exists"}},
            )
        )

        client = RegistryClient("https://registry.test", token="my-token")

        with pytest.raises(RegistryError) as exc_info:
            client.publish("myorg/tools", "content")

        assert exc_info.value.status_code == http.HTTPStatus.CONFLICT
        assert exc_info.value.code == "VERSION_EXISTS"

    @respx.mock
    def test_delete_dossier(self):
        """Should delete a dossier."""
        respx.delete("https://registry.test/api/v1/dossiers/myorg/deploy").mock(
            return_value=Response(
                200,
                json={"message": "Dossier deleted", "name": "myorg/deploy"},
            )
        )

        client = RegistryClient("https://registry.test", token="my-token")
        result = client.delete_dossier("myorg/deploy")

        assert result["name"] == "myorg/deploy"

    @respx.mock
    def test_delete_dossier_with_version(self):
        """Should delete specific version."""
        route = respx.delete("https://registry.test/api/v1/dossiers/myorg/deploy").mock(
            return_value=Response(
                200,
                json={"message": "Version deleted", "name": "myorg/deploy", "version": "1.0.0"},
            )
        )

        client = RegistryClient("https://registry.test", token="my-token")
        client.delete_dossier("myorg/deploy", version="1.0.0")

        assert route.calls[0].request.url.params["version"] == "1.0.0"

    @respx.mock
    def test_delete_dossier_not_found(self):
        """Should raise RegistryError on 404."""
        respx.delete("https://registry.test/api/v1/dossiers/myorg/missing").mock(
            return_value=Response(
                404,
                json={"error": {"code": "DOSSIER_NOT_FOUND", "message": "Dossier not found"}},
            )
        )

        client = RegistryClient("https://registry.test", token="my-token")

        with pytest.raises(RegistryError) as exc_info:
            client.delete_dossier("myorg/missing")

        assert exc_info.value.status_code == http.HTTPStatus.NOT_FOUND
        assert exc_info.value.code == "DOSSIER_NOT_FOUND"

    @respx.mock
    def test_delete_dossier_unauthorized(self):
        """Should raise on 401."""
        respx.delete("https://registry.test/api/v1/dossiers/myorg/deploy").mock(
            return_value=Response(
                401,
                json={"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}},
            )
        )

        client = RegistryClient("https://registry.test")

        with pytest.raises(RegistryError) as exc_info:
            client.delete_dossier("myorg/deploy")

        assert exc_info.value.status_code == http.HTTPStatus.UNAUTHORIZED

    @respx.mock
    def test_delete_dossier_forbidden(self):
        """Should raise on 403."""
        respx.delete("https://registry.test/api/v1/dossiers/myorg/deploy").mock(
            return_value=Response(
                403,
                json={"error": {"code": "FORBIDDEN", "message": "You do not have permission to delete this dossier"}},
            )
        )

        client = RegistryClient("https://registry.test", token="my-token")

        with pytest.raises(RegistryError) as exc_info:
            client.delete_dossier("myorg/deploy")

        assert exc_info.value.status_code == http.HTTPStatus.FORBIDDEN
        assert exc_info.value.code == "FORBIDDEN"


class TestGetRegistryUrl:
    """Tests for get_registry_url."""

    def test_returns_url_from_env(self, monkeypatch):
        """Should return URL from environment variable."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.example.com")

        url = get_registry_url()

        assert url == "https://registry.example.com"

    def test_returns_default_when_not_set(self, monkeypatch):
        """Should return default URL when not set."""
        monkeypatch.delenv("DOSSIER_REGISTRY_URL", raising=False)

        url = get_registry_url()

        assert url == "https://dossier-registry-mvp-ten.vercel.app"


class TestGetClient:
    """Tests for get_client."""

    def test_creates_client_from_env(self, monkeypatch):
        """Should create client with URL from env."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.example.com")

        client = get_client()

        assert client.base_url == "https://registry.example.com"
        assert client.token is None

    def test_creates_client_with_token(self, monkeypatch):
        """Should create client with token."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.example.com")

        client = get_client(token="my-token")

        assert client.token == "my-token"


class TestParseNameVersion:
    """Tests for parse_name_version."""

    def test_name_only(self):
        """Should return name and None for plain name."""
        name, version = parse_name_version("myorg/deploy")

        assert name == "myorg/deploy"
        assert version is None

    def test_name_with_version(self):
        """Should parse name@version."""
        name, version = parse_name_version("myorg/deploy@1.0.0")

        assert name == "myorg/deploy"
        assert version == "1.0.0"

    def test_name_with_prerelease_version(self):
        """Should handle prerelease versions."""
        name, version = parse_name_version("myorg/deploy@2.0.0-beta.1")

        assert name == "myorg/deploy"
        assert version == "2.0.0-beta.1"

    def test_nested_name_with_version(self):
        """Should handle nested names."""
        name, version = parse_name_version("org/project/workflow@1.0.0")

        assert name == "org/project/workflow"
        assert version == "1.0.0"
