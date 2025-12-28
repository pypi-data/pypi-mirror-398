"""Tests for the cache module."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from dossier_tools.cache import (
    CachedDossier,
    CacheError,
    CacheMetadata,
    cache_dossier,
    clear_cache,
    delete_cached,
    ensure_cache_dir,
    get_cache_dir,
    get_cached_path,
    get_latest_cached,
    get_meta_path,
    is_cached,
    list_cached,
    read_cached,
)


class TestCacheDir:
    """Tests for cache directory functions."""

    def test_get_cache_dir_returns_correct_path(self, tmp_path, monkeypatch):
        """Should return ~/.dossier/cache/."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        cache_dir = get_cache_dir()

        assert cache_dir == tmp_path / ".dossier" / "cache"

    def test_ensure_cache_dir_creates_directory(self, tmp_path, monkeypatch):
        """Should create cache directory if it doesn't exist."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        result = ensure_cache_dir()

        assert result.exists()
        assert result.is_dir()
        assert result == tmp_path / ".dossier" / "cache"


class TestCachePaths:
    """Tests for cache path functions."""

    def test_get_cached_path(self, tmp_path, monkeypatch):
        """Should return correct cache file path."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        path = get_cached_path("myorg/deploy", "1.0.0")

        expected = tmp_path / ".dossier" / "cache" / "myorg" / "deploy" / "1.0.0.ds.md"
        assert path == expected

    def test_get_meta_path(self, tmp_path, monkeypatch):
        """Should return correct metadata file path."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        path = get_meta_path("myorg/deploy", "1.0.0")

        expected = tmp_path / ".dossier" / "cache" / "myorg" / "deploy" / "1.0.0.meta.json"
        assert path == expected


class TestCacheDossier:
    """Tests for cache_dossier function."""

    def test_cache_dossier_writes_content_and_metadata(self, tmp_path, monkeypatch):
        """Should write both content and metadata files."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        content = "---\ntitle: Test\n---\n# Test"
        result = cache_dossier("myorg/deploy", "1.0.0", content, "https://registry.test/content")

        # Check content file
        assert result.exists()
        assert result.read_text() == content

        # Check metadata file
        meta_path = get_meta_path("myorg/deploy", "1.0.0")
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text())
        assert meta["version"] == "1.0.0"
        assert meta["source_registry_url"] == "https://registry.test/content"
        assert "cached_at" in meta

    def test_cache_dossier_creates_nested_directories(self, tmp_path, monkeypatch):
        """Should create parent directories as needed."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        result = cache_dossier("deep/nested/org/deploy", "1.0.0", "content", "https://test")

        assert result.exists()
        assert "deep/nested/org/deploy" in str(result)


class TestReadCached:
    """Tests for read_cached function."""

    def test_read_cached_returns_content(self, tmp_path, monkeypatch):
        """Should return cached content when available."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create cache
        content = "cached content"
        cache_dossier("myorg/deploy", "1.0.0", content, "https://test")

        result = read_cached("myorg/deploy", "1.0.0")

        assert result == content

    def test_read_cached_returns_none_when_not_cached(self, tmp_path, monkeypatch):
        """Should return None when not cached."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        result = read_cached("myorg/nonexistent", "1.0.0")

        assert result is None

    def test_read_cached_returns_none_when_meta_missing(self, tmp_path, monkeypatch):
        """Should return None when metadata file is missing (orphaned cache)."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create only content file (no metadata)
        cache_path = get_cached_path("myorg/deploy", "1.0.0")
        cache_path.parent.mkdir(parents=True)
        cache_path.write_text("orphaned content")

        result = read_cached("myorg/deploy", "1.0.0")

        assert result is None


class TestIsCached:
    """Tests for is_cached function."""

    def test_is_cached_true_when_exists(self, tmp_path, monkeypatch):
        """Should return True when both files exist."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        cache_dossier("myorg/deploy", "1.0.0", "content", "https://test")

        assert is_cached("myorg/deploy", "1.0.0") is True

    def test_is_cached_false_when_missing(self, tmp_path, monkeypatch):
        """Should return False when not cached."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        assert is_cached("myorg/nonexistent", "1.0.0") is False

    def test_is_cached_false_when_meta_missing(self, tmp_path, monkeypatch):
        """Should return False when metadata is missing."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create only content file
        cache_path = get_cached_path("myorg/deploy", "1.0.0")
        cache_path.parent.mkdir(parents=True)
        cache_path.write_text("content")

        assert is_cached("myorg/deploy", "1.0.0") is False


class TestGetLatestCached:
    """Tests for get_latest_cached function."""

    def test_get_latest_cached_returns_most_recent(self, tmp_path, monkeypatch):
        """Should return most recently cached version."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Cache multiple versions with different timestamps
        cache_dossier("myorg/deploy", "1.0.0", "v1", "https://test")

        # Manually create a newer entry
        cache_dir = tmp_path / ".dossier" / "cache" / "myorg" / "deploy"
        (cache_dir / "2.0.0.ds.md").write_text("v2")
        now = datetime.now(timezone.utc)
        meta = {
            "cached_at": now.isoformat(),
            "version": "2.0.0",
            "source_registry_url": "https://test",
        }
        (cache_dir / "2.0.0.meta.json").write_text(json.dumps(meta))

        result = get_latest_cached("myorg/deploy")

        assert result is not None
        assert result.version == "2.0.0"

    def test_get_latest_cached_returns_none_when_empty(self, tmp_path, monkeypatch):
        """Should return None when no versions cached."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        result = get_latest_cached("myorg/nonexistent")

        assert result is None


class TestListCached:
    """Tests for list_cached function."""

    def test_list_cached_returns_all_entries(self, tmp_path, monkeypatch):
        """Should return all cached dossiers."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        cache_dossier("myorg/deploy", "1.0.0", "content1", "https://test")
        cache_dossier("myorg/backup", "2.0.0", "content2", "https://test")
        cache_dossier("other/tool", "0.1.0", "content3", "https://test")

        result = list_cached()

        assert len(result) == 3
        names = {c.name for c in result}
        assert names == {"myorg/deploy", "myorg/backup", "other/tool"}

    def test_list_cached_empty_when_no_cache(self, tmp_path, monkeypatch):
        """Should return empty list when no cache exists."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        result = list_cached()

        assert result == []


class TestDeleteCached:
    """Tests for delete_cached function."""

    def test_delete_cached_removes_specific_version(self, tmp_path, monkeypatch):
        """Should remove specific version only."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        cache_dossier("myorg/deploy", "1.0.0", "v1", "https://test")
        cache_dossier("myorg/deploy", "2.0.0", "v2", "https://test")

        count = delete_cached("myorg/deploy", "1.0.0")

        assert count == 1
        assert not is_cached("myorg/deploy", "1.0.0")
        assert is_cached("myorg/deploy", "2.0.0")

    def test_delete_cached_removes_all_versions(self, tmp_path, monkeypatch):
        """Should remove all versions when no version specified."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        cache_dossier("myorg/deploy", "1.0.0", "v1", "https://test")
        cache_dossier("myorg/deploy", "2.0.0", "v2", "https://test")

        count = delete_cached("myorg/deploy")

        assert count == 2
        assert not is_cached("myorg/deploy", "1.0.0")
        assert not is_cached("myorg/deploy", "2.0.0")

    def test_delete_cached_returns_zero_when_not_cached(self, tmp_path, monkeypatch):
        """Should return 0 when nothing to delete."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        count = delete_cached("myorg/nonexistent", "1.0.0")

        assert count == 0


class TestClearCache:
    """Tests for clear_cache function."""

    def test_clear_cache_removes_everything(self, tmp_path, monkeypatch):
        """Should remove all cached dossiers."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        cache_dossier("myorg/deploy", "1.0.0", "content1", "https://test")
        cache_dossier("myorg/backup", "2.0.0", "content2", "https://test")

        count = clear_cache()

        assert count == 2
        assert list_cached() == []

    def test_clear_cache_returns_zero_when_empty(self, tmp_path, monkeypatch):
        """Should return 0 when cache is already empty."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        count = clear_cache()

        assert count == 0


class TestCacheMetadata:
    """Tests for CacheMetadata dataclass."""

    def test_to_dict(self):
        """Should convert to dictionary."""
        meta = CacheMetadata(
            cached_at="2025-01-01T00:00:00Z",
            version="1.0.0",
            source_registry_url="https://test",
        )

        result = meta.to_dict()

        assert result == {
            "cached_at": "2025-01-01T00:00:00Z",
            "version": "1.0.0",
            "source_registry_url": "https://test",
        }

    def test_from_dict(self):
        """Should create from dictionary."""
        data = {
            "cached_at": "2025-01-01T00:00:00Z",
            "version": "1.0.0",
            "source_registry_url": "https://test",
        }

        result = CacheMetadata.from_dict(data)

        assert result.cached_at == "2025-01-01T00:00:00Z"
        assert result.version == "1.0.0"
        assert result.source_registry_url == "https://test"


class TestCachedDossier:
    """Tests for CachedDossier dataclass."""

    def test_to_dict(self, tmp_path):
        """Should convert to dictionary with string path."""
        cached = CachedDossier(
            name="myorg/deploy",
            version="1.0.0",
            path=tmp_path / "test.ds.md",
            cached_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            source_url="https://test",
            size_bytes=100,
        )

        result = cached.to_dict()

        assert result["name"] == "myorg/deploy"
        assert result["version"] == "1.0.0"
        assert isinstance(result["path"], str)
        assert result["size_bytes"] == 100


class TestPathTraversalProtection:
    """Tests for path traversal attack prevention."""

    def test_rejects_parent_directory_traversal(self, tmp_path, monkeypatch):
        """Should reject names with '..' path traversal."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        with pytest.raises(CacheError, match="Invalid dossier name"):
            get_cached_path("../../../etc/passwd", "1.0.0")

    def test_rejects_absolute_path(self, tmp_path, monkeypatch):
        """Should reject names starting with '/'."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        with pytest.raises(CacheError, match="Invalid dossier name"):
            get_cached_path("/etc/passwd", "1.0.0")

    def test_rejects_home_expansion(self, tmp_path, monkeypatch):
        """Should reject names starting with '~'."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        with pytest.raises(CacheError, match="Invalid dossier name"):
            get_cached_path("~/.ssh/id_rsa", "1.0.0")

    def test_allows_valid_names(self, tmp_path, monkeypatch):
        """Should allow valid dossier names."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # These should not raise
        get_cached_path("myorg/deploy", "1.0.0")
        get_cached_path("org/category/tool", "2.0.0")
        get_cached_path("simple", "1.0.0")

    def test_rejects_version_with_path_traversal(self, tmp_path, monkeypatch):
        """Should reject versions with '..' path traversal."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        with pytest.raises(CacheError, match="Invalid dossier version"):
            get_cached_path("myorg/deploy", "../../../etc/passwd")

    def test_rejects_version_with_absolute_path(self, tmp_path, monkeypatch):
        """Should reject versions starting with '/'."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        with pytest.raises(CacheError, match="Invalid dossier version"):
            get_cached_path("myorg/deploy", "/etc/passwd")

    def test_rejects_version_with_home_expansion(self, tmp_path, monkeypatch):
        """Should reject versions starting with '~'."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        with pytest.raises(CacheError, match="Invalid dossier version"):
            get_cached_path("myorg/deploy", "~/.ssh/id_rsa")

    def test_rejects_version_with_slash(self, tmp_path, monkeypatch):
        """Should reject versions containing '/'."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        with pytest.raises(CacheError, match="Invalid dossier version"):
            get_cached_path("myorg/deploy", "1.0.0/malicious")

    def test_delete_cached_rejects_path_traversal(self, tmp_path, monkeypatch):
        """Should reject path traversal in delete_cached."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        with pytest.raises(CacheError, match="Invalid dossier name"):
            delete_cached("../../../etc", "passwd")

    def test_delete_cached_rejects_version_path_traversal(self, tmp_path, monkeypatch):
        """Should reject version path traversal in delete_cached."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        with pytest.raises(CacheError, match="Invalid dossier version"):
            delete_cached("myorg/deploy", "../../../etc/passwd")

    def test_get_latest_cached_rejects_path_traversal(self, tmp_path, monkeypatch):
        """Should reject path traversal in get_latest_cached."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        with pytest.raises(CacheError, match="Invalid dossier name"):
            get_latest_cached("../../../etc")
