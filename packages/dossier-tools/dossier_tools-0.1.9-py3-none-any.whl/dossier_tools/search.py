"""Search functionality for dossiers."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from .registry import RegistryClient


@dataclass
class SearchMatch:
    """A single search match."""

    field: str  # e.g., "name", "title", "content"
    context: str | None = None  # Optional context snippet for content matches


@dataclass
class SearchResult:
    """A dossier search result."""

    name: str
    title: str
    version: str
    description: str | None
    category: list[str]
    tags: list[str]
    matches: list[SearchMatch] = field(default_factory=list)

    @property
    def match_type(self) -> str:
        """Return 'metadata' or 'content' based on matches."""
        for m in self.matches:
            if m.field == "content":
                return "content"
        return "metadata"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON output."""
        return {
            "name": self.name,
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "match_type": self.match_type,
            "matches": [{"field": m.field, "context": m.context} for m in self.matches],
        }


def _fetch_all_dossiers(client: RegistryClient, per_page: int = 100) -> list[dict[str, Any]]:
    """Fetch all dossiers from the registry with automatic pagination.

    Args:
        client: Registry client
        per_page: Items per page (default: 100 for efficiency)

    Returns:
        List of all dossier metadata dicts
    """
    all_dossiers: list[dict[str, Any]] = []
    page = 1

    while True:
        result = client.list_dossiers(page=page, per_page=per_page)
        dossiers = result.get("dossiers", [])
        all_dossiers.extend(dossiers)

        pagination = result.get("pagination", {})
        total = pagination.get("total", 0)

        if len(all_dossiers) >= total or not dossiers:
            break

        page += 1

    return all_dossiers


def _match_in_text(query: str, text: str | None) -> bool:
    """Check if query matches in text (case-insensitive)."""
    if not text:
        return False
    return query.lower() in text.lower()


def _match_in_list(query: str, items: list[str] | None) -> bool:
    """Check if query matches any item in list (case-insensitive)."""
    if not items:
        return False
    query_lower = query.lower()
    return any(query_lower in str(item).lower() for item in items)


def search_metadata(dossier: dict[str, Any], query: str) -> list[SearchMatch]:
    """Search dossier metadata for query.

    Searches: name, title, description, category, tags

    Returns:
        List of SearchMatch for each matching field
    """
    matches = []

    # Search text fields
    for field_name in ("name", "title", "description"):
        value = dossier.get(field_name)
        if _match_in_text(query, value):
            matches.append(SearchMatch(field=field_name))

    # Search list fields
    for field_name in ("category", "tags"):
        value = dossier.get(field_name, [])
        if _match_in_list(query, value):
            matches.append(SearchMatch(field=field_name))

    return matches


def search_content(content: str, query: str) -> SearchMatch | None:
    """Search dossier content for query.

    Returns:
        SearchMatch with context snippet, or None if not found
    """
    query_lower = query.lower()
    content_lower = content.lower()

    idx = content_lower.find(query_lower)
    if idx == -1:
        return None

    # Extract context (50 chars before/after)
    start = max(0, idx - 50)
    end = min(len(content), idx + len(query) + 50)
    context = content[start:end]

    # Clean up context (add ellipsis)
    if start > 0:
        context = "..." + context
    if end < len(content):
        context = context + "..."

    return SearchMatch(field="content", context=context)


def _fetch_content_from_url(url: str, timeout: float = 10.0) -> str | None:
    """Fetch content from a CDN URL.

    Args:
        url: CDN URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Content string or None on error
    """
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    else:
        return response.text


def search_dossiers(
    client: RegistryClient,
    query: str,
    *,
    include_content: bool = False,
    limit: int | None = None,
    max_workers: int = 5,
) -> list[SearchResult]:
    """Search dossiers by query.

    Args:
        client: Registry client
        query: Search query
        include_content: If True, also search inside dossier content
        limit: Maximum number of results to return
        max_workers: Number of parallel workers for content fetching

    Returns:
        List of SearchResult
    """
    # Phase 1: Fetch all dossiers and search metadata
    all_dossiers = _fetch_all_dossiers(client)

    results: list[SearchResult] = []
    needs_content_search: list[tuple[dict[str, Any], SearchResult]] = []

    for dossier in all_dossiers:
        matches = search_metadata(dossier, query)

        result = SearchResult(
            name=dossier.get("name", ""),
            title=dossier.get("title", ""),
            version=dossier.get("version", ""),
            description=dossier.get("description"),
            category=dossier.get("category") or [],
            tags=dossier.get("tags") or [],
            matches=matches,
        )

        if matches:
            results.append(result)
        elif include_content and dossier.get("url"):
            # Queue for content search
            needs_content_search.append((dossier, result))

    # Phase 2: Content search (if enabled)
    if include_content and needs_content_search:

        def fetch_and_search(item: tuple[dict[str, Any], SearchResult]) -> SearchResult | None:
            dossier, result = item
            url = dossier.get("url")
            if not url:
                return None

            content = _fetch_content_from_url(url)
            if not content:
                return None

            match = search_content(content, query)
            if match:
                result.matches.append(match)
                return result
            return None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_and_search, item): item for item in needs_content_search}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

    # Apply limit
    if limit and len(results) > limit:
        results = results[:limit]

    return results


__all__ = [
    "SearchMatch",
    "SearchResult",
    "search_content",
    "search_dossiers",
    "search_metadata",
]
