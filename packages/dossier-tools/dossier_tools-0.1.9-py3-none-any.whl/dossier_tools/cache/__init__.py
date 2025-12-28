"""Cache management for dossier files."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from ..logging import get_logger
from ..signing import get_dossier_dir

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger("cache")

# Minimum path parts for a valid cache entry (e.g., myorg/deploy/1.0.0.meta.json)
_MIN_PATH_PARTS = 2


class CacheError(Exception):
    """Base exception for cache operations."""


@dataclass
class CachedDossier:
    """Metadata for a cached dossier."""

    name: str
    version: str
    path: Path
    cached_at: datetime
    source_url: str
    size_bytes: int

    def to_dict(self) -> dict:
        """Convert to dictionary for display."""
        return {
            "name": self.name,
            "version": self.version,
            "path": str(self.path),
            "cached_at": self.cached_at.isoformat(),
            "source_url": self.source_url,
            "size_bytes": self.size_bytes,
        }


@dataclass
class CacheMetadata:
    """Metadata stored alongside cached dossier."""

    cached_at: str
    version: str
    source_registry_url: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CacheMetadata:
        """Create from dictionary."""
        return cls(
            cached_at=data["cached_at"],
            version=data["version"],
            source_registry_url=data["source_registry_url"],
        )


def get_cache_dir() -> Path:
    """Return ~/.dossier/cache/ directory path.

    Does not create the directory - use ensure_cache_dir() for that.
    """
    return get_dossier_dir() / "cache"


def ensure_cache_dir() -> Path:
    """Return ~/.dossier/cache/ directory, creating if needed.

    Raises:
        CacheError: If directory cannot be created due to permissions.
    """
    cache_dir = get_cache_dir()
    try:
        cache_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    except PermissionError as e:
        msg = f"Cannot create cache directory: {e}"
        raise CacheError(msg) from e
    return cache_dir


def _validate_path_component(value: str, component_type: str) -> None:
    """Validate that a path component doesn't contain path traversal attempts.

    Args:
        value: The value to validate (name or version)
        component_type: Description for error message ('name' or 'version')

    Raises:
        CacheError: If value contains dangerous path components.
    """
    # Check for path traversal attempts
    if ".." in value or value.startswith(("/", "~")):
        msg = f"Invalid dossier {component_type}: {value}"
        raise CacheError(msg)

    # Version cannot contain slashes at all
    if component_type == "version" and "/" in value:
        msg = f"Invalid dossier {component_type}: {value}"
        raise CacheError(msg)


def get_cached_path(name: str, version: str) -> Path:
    """Return path for cached dossier file.

    Args:
        name: Dossier name (e.g., 'myorg/deploy')
        version: Version string (e.g., '1.0.0')

    Returns:
        Path like ~/.dossier/cache/myorg/deploy/1.0.0.ds.md

    Raises:
        CacheError: If name or version contains path traversal attempts.
    """
    _validate_path_component(name, "name")
    _validate_path_component(version, "version")
    return get_cache_dir() / name / f"{version}.ds.md"


def get_meta_path(name: str, version: str) -> Path:
    """Return path for cache metadata file.

    Args:
        name: Dossier name (e.g., 'myorg/deploy')
        version: Version string (e.g., '1.0.0')

    Returns:
        Path like ~/.dossier/cache/myorg/deploy/1.0.0.meta.json

    Raises:
        CacheError: If name or version contains path traversal attempts.
    """
    _validate_path_component(name, "name")
    _validate_path_component(version, "version")
    return get_cache_dir() / name / f"{version}.meta.json"


def cache_dossier(name: str, version: str, content: str, source_url: str) -> Path:
    """Write dossier content to cache.

    Args:
        name: Dossier name (e.g., 'myorg/deploy')
        version: Version string (e.g., '1.0.0')
        content: Full .ds.md file content
        source_url: URL the content was fetched from

    Returns:
        Path to the cached file

    Raises:
        CacheError: If write fails due to permissions or disk space.
    """
    ensure_cache_dir()

    cache_path = get_cached_path(name, version)
    meta_path = get_meta_path(name, version)

    # Create parent directories
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        msg = f"Cannot create cache directory for {name}: {e}"
        raise CacheError(msg) from e

    # Write content file
    try:
        cache_path.write_text(content, encoding="utf-8")
    except (PermissionError, OSError) as e:
        msg = f"Cannot write cache file: {e}"
        raise CacheError(msg) from e

    # Write metadata
    metadata = CacheMetadata(
        cached_at=datetime.now(timezone.utc).isoformat(),
        version=version,
        source_registry_url=source_url,
    )
    try:
        meta_path.write_text(json.dumps(metadata.to_dict(), indent=2), encoding="utf-8")
    except (PermissionError, OSError) as e:
        # Clean up content file if metadata write fails
        cache_path.unlink(missing_ok=True)
        msg = f"Cannot write cache metadata: {e}"
        raise CacheError(msg) from e

    logger.debug("Cached %s@%s to %s", name, version, cache_path)
    return cache_path


def read_cached(name: str, version: str) -> str | None:
    """Read dossier content from cache.

    Args:
        name: Dossier name (e.g., 'myorg/deploy')
        version: Version string (e.g., '1.0.0')

    Returns:
        Content string if cached, None otherwise.

    Note:
        Returns None if metadata file is missing (orphaned cache file).
    """
    cache_path = get_cached_path(name, version)
    meta_path = get_meta_path(name, version)

    # Both files must exist
    if not cache_path.exists() or not meta_path.exists():
        return None

    try:
        return cache_path.read_text(encoding="utf-8")
    except (PermissionError, OSError) as e:
        logger.warning("Cannot read cache file %s: %s", cache_path, e)
        return None


def is_cached(name: str, version: str) -> bool:
    """Check if a specific version is cached.

    Args:
        name: Dossier name (e.g., 'myorg/deploy')
        version: Version string (e.g., '1.0.0')

    Returns:
        True if both content and metadata files exist.
    """
    return get_cached_path(name, version).exists() and get_meta_path(name, version).exists()


def get_latest_cached(name: str) -> CachedDossier | None:
    """Get the most recently cached version for a dossier.

    Args:
        name: Dossier name (e.g., 'myorg/deploy')

    Returns:
        CachedDossier for most recent version, or None if not cached.

    Raises:
        CacheError: If name contains path traversal attempts.
    """
    _validate_path_component(name, "name")
    dossier_dir = get_cache_dir() / name

    if not dossier_dir.exists():
        return None

    # Find all cached versions
    cached_versions: list[CachedDossier] = []

    for meta_file in dossier_dir.glob("*.meta.json"):
        version = meta_file.stem.replace(".meta", "")
        content_file = dossier_dir / f"{version}.ds.md"

        if not content_file.exists():
            continue

        try:
            meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
            metadata = CacheMetadata.from_dict(meta_data)
            cached_at = datetime.fromisoformat(metadata.cached_at)

            cached_versions.append(
                CachedDossier(
                    name=name,
                    version=metadata.version,
                    path=content_file,
                    cached_at=cached_at,
                    source_url=metadata.source_registry_url,
                    size_bytes=content_file.stat().st_size,
                )
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Invalid cache metadata %s: %s", meta_file, e)
            continue

    if not cached_versions:
        return None

    # Return most recently cached
    return max(cached_versions, key=lambda c: c.cached_at)


def list_cached() -> list[CachedDossier]:
    """List all cached dossiers.

    Returns:
        List of CachedDossier objects for all valid cached entries.
    """
    cache_dir = get_cache_dir()

    if not cache_dir.exists():
        return []

    cached: list[CachedDossier] = []

    # Walk through cache directory structure
    for meta_file in cache_dir.glob("**/*.meta.json"):
        # Extract name and version from path
        # Path: ~/.dossier/cache/myorg/deploy/1.0.0.meta.json
        rel_path = meta_file.relative_to(cache_dir)
        parts = list(rel_path.parts)

        if len(parts) < _MIN_PATH_PARTS:
            continue

        version = parts[-1].replace(".meta.json", "")
        name = "/".join(parts[:-1])

        content_file = meta_file.parent / f"{version}.ds.md"

        if not content_file.exists():
            continue

        try:
            meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
            metadata = CacheMetadata.from_dict(meta_data)
            cached_at = datetime.fromisoformat(metadata.cached_at)

            cached.append(
                CachedDossier(
                    name=name,
                    version=metadata.version,
                    path=content_file,
                    cached_at=cached_at,
                    source_url=metadata.source_registry_url,
                    size_bytes=content_file.stat().st_size,
                )
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Invalid cache metadata %s: %s", meta_file, e)
            continue

    # Sort by name, then version
    return sorted(cached, key=lambda c: (c.name, c.version))


def delete_cached(name: str, version: str | None = None) -> int:
    """Delete cached dossier(s).

    Args:
        name: Dossier name (e.g., 'myorg/deploy')
        version: Optional specific version. If None, deletes all versions.

    Returns:
        Number of versions deleted.

    Raises:
        CacheError: If name or version contains path traversal attempts.
    """
    _validate_path_component(name, "name")
    if version:
        _validate_path_component(version, "version")

    cache_dir = get_cache_dir()
    dossier_dir = cache_dir / name
    deleted = 0

    if not dossier_dir.exists():
        return 0

    if version:
        # Delete specific version
        content_file = dossier_dir / f"{version}.ds.md"
        meta_file = dossier_dir / f"{version}.meta.json"

        if content_file.exists():
            content_file.unlink()
            deleted += 1
        if meta_file.exists():
            meta_file.unlink()

        # Clean up empty directories
        _cleanup_empty_dirs(dossier_dir, cache_dir)
    else:
        # Delete all versions (entire dossier directory)
        for meta_file in dossier_dir.glob("*.meta.json"):
            version_str = meta_file.stem.replace(".meta", "")
            content_file = dossier_dir / f"{version_str}.ds.md"

            if content_file.exists():
                content_file.unlink()
                deleted += 1
            meta_file.unlink()

        # Remove the dossier directory and any empty parents
        _cleanup_empty_dirs(dossier_dir, cache_dir)

    logger.debug("Deleted %d cached version(s) of %s", deleted, name)
    return deleted


def clear_cache() -> int:
    """Delete all cached dossiers.

    Returns:
        Number of dossiers deleted.
    """
    cache_dir = get_cache_dir()

    if not cache_dir.exists():
        return 0

    # Count before clearing
    cached = list_cached()
    count = len(cached)

    # Remove entire cache directory
    shutil.rmtree(cache_dir, ignore_errors=True)

    logger.debug("Cleared cache: %d dossiers removed", count)
    return count


def delete_older_than(days: int) -> int:
    """Delete cached dossiers older than specified days.

    Args:
        days: Number of days. Entries older than this are deleted.

    Returns:
        Number of dossiers deleted.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    deleted = 0
    for cached in list_cached():
        if cached.cached_at < cutoff:
            delete_cached(cached.name, cached.version)
            deleted += 1

    return deleted


def _cleanup_empty_dirs(start: Path, stop: Path) -> None:
    """Remove empty directories from start up to (but not including) stop."""
    current = start
    while current != stop and current.exists():
        if not any(current.iterdir()):
            current.rmdir()
            current = current.parent
        else:
            break


__all__ = [
    "CacheError",
    "CacheMetadata",
    "CachedDossier",
    "cache_dossier",
    "clear_cache",
    "delete_cached",
    "delete_older_than",
    "ensure_cache_dir",
    "get_cache_dir",
    "get_cached_path",
    "get_latest_cached",
    "is_cached",
    "list_cached",
    "read_cached",
]
