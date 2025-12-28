"""Tests for the OAuth module."""

import base64
import json
from unittest.mock import patch

import pytest

from dossier_tools.registry.oauth import (
    OAuthError,
    OAuthResult,
    run_oauth_flow,
)


def _make_jwt(payload: dict) -> str:
    """Create a minimal JWT for testing (header.payload.signature)."""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(b"fake-signature").rstrip(b"=").decode()
    return f"{header}.{body}.{sig}"


def _encode_display_code(token: str) -> str:
    """Encode JWT as display code (base64url)."""
    return base64.urlsafe_b64encode(token.encode()).rstrip(b"=").decode()


class TestRunOAuthFlow:
    """Tests for run_oauth_flow."""

    def test_successful_flow(self):
        """Should complete OAuth flow successfully."""
        jwt = _make_jwt(
            {
                "sub": "alice",
                "orgs": ["org1", "org2"],
                "email": "alice@example.com",
            }
        )
        code = _encode_display_code(jwt)

        def mock_prompt(_msg):
            return code

        with patch("webbrowser.open", return_value=True):
            result = run_oauth_flow("https://registry.test", prompt_func=mock_prompt)

        assert isinstance(result, OAuthResult)
        assert result.token == jwt
        assert result.username == "alice"
        assert result.orgs == ["org1", "org2"]
        assert result.email == "alice@example.com"

    def test_empty_code(self):
        """Should raise OAuthError for empty code."""

        def mock_prompt(_msg):
            return ""

        with patch("webbrowser.open", return_value=True), pytest.raises(OAuthError) as exc_info:
            run_oauth_flow("https://registry.test", prompt_func=mock_prompt)

        assert "No code provided" in str(exc_info.value)

    def test_invalid_base64(self):
        """Should raise OAuthError for invalid base64."""

        def mock_prompt(_msg):
            return "!!invalid!!"

        with patch("webbrowser.open", return_value=True), pytest.raises(OAuthError) as exc_info:
            run_oauth_flow("https://registry.test", prompt_func=mock_prompt)

        assert "Invalid code format" in str(exc_info.value)

    def test_invalid_jwt_format(self):
        """Should raise OAuthError for invalid JWT format."""
        code = _encode_display_code("not.a.valid.jwt.too.many.parts")

        def mock_prompt(_msg):
            return code

        with patch("webbrowser.open", return_value=True), pytest.raises(OAuthError) as exc_info:
            run_oauth_flow("https://registry.test", prompt_func=mock_prompt)

        assert "Invalid token" in str(exc_info.value)

    def test_missing_username(self):
        """Should raise OAuthError if username (sub) missing."""
        jwt = _make_jwt({"orgs": []})
        code = _encode_display_code(jwt)

        def mock_prompt(_msg):
            return code

        with patch("webbrowser.open", return_value=True), pytest.raises(OAuthError) as exc_info:
            run_oauth_flow("https://registry.test", prompt_func=mock_prompt)

        assert "missing username" in str(exc_info.value)

    def test_defaults_orgs_to_empty(self):
        """Should default orgs to empty list if missing."""
        jwt = _make_jwt({"sub": "alice"})
        code = _encode_display_code(jwt)

        def mock_prompt(_msg):
            return code

        with patch("webbrowser.open", return_value=True):
            result = run_oauth_flow("https://registry.test", prompt_func=mock_prompt)

        assert result.orgs == []

    def test_browser_fails_prints_url(self, capsys):
        """Should print URL if browser fails to open."""
        jwt = _make_jwt({"sub": "alice"})
        code = _encode_display_code(jwt)

        def mock_prompt(_msg):
            return code

        with patch("webbrowser.open", return_value=False):
            run_oauth_flow("https://registry.test", prompt_func=mock_prompt)

        captured = capsys.readouterr()
        assert "https://registry.test/auth/login" in captured.out
