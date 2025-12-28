"""Authentication credentials management."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..signing import get_dossier_dir

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Credentials:
    """Stored authentication credentials."""

    token: str
    username: str
    orgs: list[str]
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Credentials:
        """Create from dictionary."""
        return cls(
            token=data["token"],
            username=data["username"],
            orgs=data.get("orgs", []),
            expires_at=data.get("expires_at"),
        )

    def is_expired(self) -> bool:
        """Check if credentials are expired."""
        if not self.expires_at:
            return False
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.now(expires.tzinfo) > expires
        except (ValueError, TypeError):
            return False


def get_credentials_path() -> Path:
    """Get path to credentials file."""
    return get_dossier_dir() / "credentials"


def save_credentials(credentials: Credentials) -> None:
    """Save credentials to file with secure permissions (0600)."""
    path = get_credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(credentials.to_dict(), indent=2))
    path.chmod(0o600)


def load_credentials() -> Credentials | None:
    """Load credentials from file, or None if not exists."""
    path = get_credentials_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return Credentials.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None


def delete_credentials() -> bool:
    """Delete credentials file. Returns True if deleted, False if didn't exist."""
    path = get_credentials_path()
    if path.exists():
        path.unlink()
        return True
    return False


# Backwards compatibility aliases
def get_token_path() -> Path:
    """Get path to credentials file (backwards compat)."""
    return get_credentials_path()


def save_token(token: str) -> None:
    """Save token only (backwards compat - prefer save_credentials)."""
    save_credentials(Credentials(token=token, username="unknown", orgs=[]))


def load_token() -> str | None:
    """Load token from credentials file (backwards compat)."""
    creds = load_credentials()
    return creds.token if creds else None


def delete_token() -> bool:
    """Delete credentials file (backwards compat)."""
    return delete_credentials()


__all__ = [
    "Credentials",
    "delete_credentials",
    "delete_token",
    "get_credentials_path",
    "get_token_path",
    "load_credentials",
    "load_token",
    "save_credentials",
    "save_token",
]
