"""HTTP client for the Dossier Registry API."""

from __future__ import annotations

import contextlib
import os
from typing import Any

import httpx

from ..logging import get_logger

logger = get_logger("registry")


class RegistryError(Exception):
    """Base exception for registry errors."""

    def __init__(self, message: str, status_code: int | None = None, code: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class RegistryClient:
    """HTTP client for the Dossier Registry API."""

    def __init__(self, base_url: str, token: str | None = None):
        """Initialize the registry client.

        Args:
            base_url: Registry base URL (e.g., https://registry.dossier.dev)
            token: Optional Bearer token for authenticated requests
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._client = httpx.Client(
            base_url=f"{self.base_url}/api/v1",
            headers=self._build_headers(),
            timeout=30.0,
            follow_redirects=True,
        )
        logger.debug("Initialized registry client: %s", self.base_url)

    def _build_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response, raising on errors."""
        if response.is_error:
            error_data = None
            with contextlib.suppress(Exception):
                error_data = response.json().get("error", {})

            message = f"Registry request failed: {response.status_code} {response.reason_phrase}"
            code = None
            if error_data:
                message = error_data.get("message", message)
                code = error_data.get("code")

            logger.warning("API error: %s (code=%s)", message, code)
            raise RegistryError(message, status_code=response.status_code, code=code)

        return response.json()

    def list_dossiers(self, category: str | None = None, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        """List dossiers from the registry.

        Args:
            category: Optional category filter
            page: Page number (default: 1)
            per_page: Items per page (default: 20)

        Returns:
            Dict with 'dossiers' list and 'pagination' info
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if category:
            params["category"] = category

        logger.debug("Listing dossiers: category=%s page=%d", category, page)
        response = self._client.get("/dossiers", params=params)
        return self._handle_response(response)

    def get_dossier(self, name: str, version: str | None = None) -> dict[str, Any]:
        """Get metadata for a dossier.

        Args:
            name: Dossier name (e.g., 'myorg/deploy')
            version: Optional version (default: latest)

        Returns:
            Dossier metadata dict
        """
        params = {}
        if version:
            params["version"] = version

        logger.debug("Getting dossier: %s@%s", name, version or "latest")
        response = self._client.get(f"/dossiers/{name}", params=params)
        return self._handle_response(response)

    def pull_content(self, name: str, version: str | None = None) -> tuple[str, str | None]:
        """Download dossier content.

        Args:
            name: Dossier name (e.g., 'myorg/deploy')
            version: Optional version (default: latest)

        Returns:
            Tuple of (content, digest) where digest is from X-Dossier-Digest header
        """
        params = {}
        if version:
            params["version"] = version

        logger.debug("Pulling content: %s@%s", name, version or "latest")
        response = self._client.get(f"/dossiers/{name}/content", params=params)

        if response.is_error:
            error_data = None
            with contextlib.suppress(Exception):
                error_data = response.json().get("error", {})

            message = f"Failed to download dossier '{name}': {response.status_code} {response.reason_phrase}"
            code = None
            if error_data:
                message = error_data.get("message", message)
                code = error_data.get("code")

            logger.warning("Download failed: %s (code=%s)", message, code)
            raise RegistryError(message, status_code=response.status_code, code=code)

        content = response.text
        digest = response.headers.get("X-Dossier-Digest")

        logger.debug("Downloaded %d bytes, digest=%s", len(content), digest)
        return content, digest

    def exchange_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Exchange OAuth code for access token.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: The redirect URI used in the auth request

        Returns:
            Dict with 'access_token' and optionally 'refresh_token'
        """
        logger.debug("Exchanging OAuth code")
        response = self._client.post(
            "/auth/token",
            json={"code": code, "redirect_uri": redirect_uri},
        )
        return self._handle_response(response)

    def get_me(self) -> dict[str, Any]:
        """Get current user info.

        Returns:
            Dict with user info (username, email, etc.)

        Raises:
            RegistryError: If not authenticated (401)
        """
        logger.debug("Getting current user info")
        response = self._client.get("/me")
        return self._handle_response(response)

    def publish(
        self,
        namespace: str,
        content: str,
        changelog: str | None = None,
    ) -> dict[str, Any]:
        """Publish a dossier to the registry.

        Args:
            namespace: Target namespace (e.g., 'myorg/tools')
            content: Full .ds.md file content
            changelog: Optional changelog message

        Returns:
            Dict with published dossier info

        Raises:
            RegistryError: If publish fails (401, 403, 409, etc.)
        """
        data: dict[str, Any] = {"namespace": namespace, "content": content}
        if changelog:
            data["changelog"] = changelog

        logger.debug("Publishing to namespace: %s (%d bytes)", namespace, len(content))
        response = self._client.post("/dossiers", json=data)
        result = self._handle_response(response)
        logger.info("Published: %s", result.get("name", namespace))
        return result

    def delete_dossier(self, name: str, version: str | None = None) -> dict[str, Any]:
        """Delete a dossier from the registry.

        Args:
            name: Dossier name (e.g., 'myorg/deploy')
            version: Optional specific version to delete. If not provided,
                     deletes the entire dossier (all versions).

        Returns:
            Dict with deletion confirmation

        Raises:
            RegistryError: If deletion fails (401, 403, 404, etc.)
        """
        params = {}
        if version:
            params["version"] = version

        target = f"{name}@{version}" if version else name
        logger.debug("Deleting dossier: %s", target)
        response = self._client.delete(f"/dossiers/{name}", params=params)
        result = self._handle_response(response)
        logger.info("Deleted: %s", target)
        return result

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> RegistryClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


DEFAULT_REGISTRY_URL = "https://dossier-registry-mvp-ten.vercel.app"


def get_registry_url() -> str:
    """Get registry URL from environment or use default.

    Returns:
        Registry URL (from DOSSIER_REGISTRY_URL env var or default)
    """
    return os.environ.get("DOSSIER_REGISTRY_URL", DEFAULT_REGISTRY_URL)


def get_client(token: str | None = None) -> RegistryClient:
    """Create a registry client from environment configuration.

    Args:
        token: Optional auth token (for authenticated requests)

    Returns:
        RegistryClient instance
    """
    return RegistryClient(get_registry_url(), token=token)


def parse_name_version(name: str) -> tuple[str, str | None]:
    """Parse a name@version string.

    Args:
        name: Dossier name, optionally with @version suffix

    Returns:
        Tuple of (name, version) where version may be None

    Examples:
        >>> parse_name_version("myorg/deploy")
        ('myorg/deploy', None)
        >>> parse_name_version("myorg/deploy@1.0.0")
        ('myorg/deploy', '1.0.0')
    """
    if "@" in name:
        parts = name.rsplit("@", 1)
        return parts[0], parts[1]
    return name, None


__all__ = [
    "RegistryClient",
    "RegistryError",
    "get_client",
    "get_registry_url",
    "parse_name_version",
]
