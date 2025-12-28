"""OAuth authentication flow for registry login."""

from __future__ import annotations

import base64
import json
import webbrowser
from dataclasses import dataclass
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from collections.abc import Callable


class OAuthError(Exception):
    """OAuth authentication error."""


@dataclass
class OAuthResult:
    """Result of OAuth authentication."""

    token: str
    username: str
    orgs: list[str]
    email: str | None = None


BASE64_BLOCK_SIZE = 4


def _decode_base64url(data: str) -> bytes:
    """Decode base64url string, adding padding if needed."""
    padding = BASE64_BLOCK_SIZE - len(data) % BASE64_BLOCK_SIZE
    if padding != BASE64_BLOCK_SIZE:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def run_oauth_flow(
    registry_url: str,
    prompt_func: Callable[[str], str] | None = None,
) -> OAuthResult:
    """Run the OAuth flow using copy/paste method.

    Opens a browser for GitHub authentication. The registry displays a code
    that the user copies and pastes back into the CLI.

    Args:
        registry_url: Base URL of the registry
        prompt_func: Function to prompt for code (default: click.prompt).
                     Useful for testing or custom prompts.

    Returns:
        OAuthResult with token and user info

    Raises:
        OAuthError: If authentication fails
    """
    if prompt_func is None:
        prompt_func = click.prompt

    # Build OAuth URL - redirect goes to registry, not localhost
    auth_url = f"{registry_url}/auth/login"

    # Try to open browser
    if not webbrowser.open(auth_url):
        # Browser failed to open, print URL for manual copy
        click.echo(f"Open this URL in your browser:\n  {auth_url}")

    # Prompt for code
    click.echo()
    code = prompt_func("Enter the code from your browser").strip()

    if not code:
        raise OAuthError("No code provided")

    # The code is a base64url-encoded JWT
    # Decode it to get the JWT, then decode the JWT payload for user info
    try:
        token = _decode_base64url(code).decode("utf-8")
    except Exception as e:
        msg = f"Invalid code format: {e}"
        raise OAuthError(msg) from e

    # Decode JWT payload (middle part) to get user info
    parts = token.split(".")
    if len(parts) != 3:  # noqa: PLR2004
        raise OAuthError("Invalid token format")

    try:
        payload = json.loads(_decode_base64url(parts[1]))
    except Exception as e:
        msg = f"Invalid token: {e}"
        raise OAuthError(msg) from e

    # Extract user info from JWT claims
    username = payload.get("sub")
    if not username:
        raise OAuthError("Invalid token: missing username")

    return OAuthResult(
        token=token,
        username=username,
        orgs=payload.get("orgs", []),
        email=payload.get("email"),
    )


__all__ = [
    "OAuthError",
    "OAuthResult",
    "run_oauth_flow",
]
