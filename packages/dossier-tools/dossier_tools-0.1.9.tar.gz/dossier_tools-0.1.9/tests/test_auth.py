"""Tests for the auth module."""

import json
import stat

from dossier_tools.registry import (
    Credentials,
    delete_credentials,
    delete_token,
    get_credentials_path,
    get_token_path,
    load_credentials,
    load_token,
    save_credentials,
    save_token,
)


class TestCredentials:
    """Tests for Credentials dataclass."""

    def test_to_dict(self):
        """Should convert to dictionary."""
        creds = Credentials(
            token="my-token",
            username="alice",
            orgs=["org1", "org2"],
            expires_at="2025-12-04T10:00:00Z",
        )

        result = creds.to_dict()

        assert result["token"] == "my-token"
        assert result["username"] == "alice"
        assert result["orgs"] == ["org1", "org2"]
        assert result["expires_at"] == "2025-12-04T10:00:00Z"

    def test_from_dict(self):
        """Should create from dictionary."""
        data = {
            "token": "my-token",
            "username": "alice",
            "orgs": ["org1"],
        }

        creds = Credentials.from_dict(data)

        assert creds.token == "my-token"
        assert creds.username == "alice"
        assert creds.orgs == ["org1"]
        assert creds.expires_at is None

    def test_is_expired_not_expired(self):
        """Should return False for future expiry."""
        creds = Credentials(
            token="my-token",
            username="alice",
            orgs=[],
            expires_at="2099-12-04T10:00:00+00:00",
        )

        assert creds.is_expired() is False

    def test_is_expired_expired(self):
        """Should return True for past expiry."""
        creds = Credentials(
            token="my-token",
            username="alice",
            orgs=[],
            expires_at="2020-01-01T00:00:00+00:00",
        )

        assert creds.is_expired() is True

    def test_is_expired_no_expiry(self):
        """Should return False if no expiry set."""
        creds = Credentials(token="my-token", username="alice", orgs=[])

        assert creds.is_expired() is False


class TestSaveCredentials:
    """Tests for save_credentials."""

    def test_creates_file(self, tmp_path, monkeypatch):
        """Should create credentials file."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        creds = Credentials(token="my-token", username="alice", orgs=["org1"])
        save_credentials(creds)

        creds_path = tmp_path / ".dossier" / "credentials"
        assert creds_path.exists()

        data = json.loads(creds_path.read_text())
        assert data["token"] == "my-token"
        assert data["username"] == "alice"
        assert data["orgs"] == ["org1"]

    def test_sets_permissions(self, tmp_path, monkeypatch):
        """Should set file permissions to 0600."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        creds = Credentials(token="my-token", username="alice", orgs=[])
        save_credentials(creds)

        creds_path = tmp_path / ".dossier" / "credentials"
        mode = creds_path.stat().st_mode & 0o777
        assert mode == stat.S_IRUSR | stat.S_IWUSR


class TestLoadCredentials:
    """Tests for load_credentials."""

    def test_returns_saved_credentials(self, tmp_path, monkeypatch):
        """Should return saved credentials."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        creds = Credentials(token="my-token", username="alice", orgs=["org1"])
        save_credentials(creds)
        loaded = load_credentials()

        assert loaded is not None
        assert loaded.token == "my-token"
        assert loaded.username == "alice"
        assert loaded.orgs == ["org1"]

    def test_returns_none_when_missing(self, tmp_path, monkeypatch):
        """Should return None if no credentials file."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        result = load_credentials()

        assert result is None

    def test_returns_none_for_invalid_json(self, tmp_path, monkeypatch):
        """Should return None if credentials file is invalid."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text("not json")

        result = load_credentials()

        assert result is None


class TestDeleteCredentials:
    """Tests for delete_credentials."""

    def test_removes_file(self, tmp_path, monkeypatch):
        """Should remove credentials file."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        creds = Credentials(token="my-token", username="alice", orgs=[])
        save_credentials(creds)
        result = delete_credentials()

        creds_path = tmp_path / ".dossier" / "credentials"
        assert result is True
        assert not creds_path.exists()

    def test_returns_false_when_missing(self, tmp_path, monkeypatch):
        """Should return False if no credentials file."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        result = delete_credentials()

        assert result is False


class TestGetCredentialsPath:
    """Tests for get_credentials_path."""

    def test_returns_correct_path(self, tmp_path, monkeypatch):
        """Should return path to credentials file."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        path = get_credentials_path()

        assert path == tmp_path / ".dossier" / "credentials"


# Backwards compatibility tests


class TestBackwardsCompat:
    """Tests for backwards compatibility functions."""

    def test_save_token_creates_credentials(self, tmp_path, monkeypatch):
        """save_token should create credentials with unknown username."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        save_token("my-token")

        creds = load_credentials()
        assert creds is not None
        assert creds.token == "my-token"
        assert creds.username == "unknown"

    def test_load_token_returns_token(self, tmp_path, monkeypatch):
        """load_token should return token from credentials."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        creds = Credentials(token="my-token", username="alice", orgs=[])
        save_credentials(creds)
        token = load_token()

        assert token == "my-token"

    def test_delete_token_deletes_credentials(self, tmp_path, monkeypatch):
        """delete_token should delete credentials file."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        creds = Credentials(token="my-token", username="alice", orgs=[])
        save_credentials(creds)
        result = delete_token()

        assert result is True
        assert load_credentials() is None

    def test_get_token_path_returns_credentials_path(self, tmp_path, monkeypatch):
        """get_token_path should return credentials path."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        path = get_token_path()

        assert path == tmp_path / ".dossier" / "credentials"
