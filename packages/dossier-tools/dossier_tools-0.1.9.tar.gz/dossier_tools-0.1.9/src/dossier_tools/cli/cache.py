"""Cache management CLI commands for dossier-tools."""

from __future__ import annotations

import json
import sys

import click

from ..cache import (
    CacheError,
    clear_cache,
    delete_cached,
    delete_older_than,
    list_cached,
)
from . import main

# Size constants for human-readable formatting
_KB = 1024
_MB = 1024 * 1024


@main.group()
def cache() -> None:
    """Manage local dossier cache."""


@cache.command("list")
@click.option("--size", is_flag=True, help="Show file sizes")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def cache_list(size: bool, as_json: bool) -> None:
    """List cached dossiers."""
    try:
        cached = list_cached()
    except CacheError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps([c.to_dict() for c in cached]))
        return

    if not cached:
        click.echo("No cached dossiers.")
        return

    # Print as table
    if size:
        click.echo(f"{'NAME':<30} {'VERSION':<12} {'SIZE':<10} {'CACHED AT'}")
        click.echo("-" * 70)
        for c in cached:
            size_str = _format_size(c.size_bytes)
            cached_at = c.cached_at.strftime("%Y-%m-%d %H:%M")
            click.echo(f"{c.name:<30} {c.version:<12} {size_str:<10} {cached_at}")
    else:
        click.echo(f"{'NAME':<30} {'VERSION':<12} {'CACHED AT'}")
        click.echo("-" * 60)
        for c in cached:
            cached_at = c.cached_at.strftime("%Y-%m-%d %H:%M")
            click.echo(f"{c.name:<30} {c.version:<12} {cached_at}")

    click.echo()
    click.echo(f"Total: {len(cached)} cached dossier(s)")


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < _KB:
        return f"{size_bytes}B"
    if size_bytes < _MB:
        return f"{size_bytes / _KB:.1f}KB"
    return f"{size_bytes / _MB:.1f}MB"


def _clean_all(yes: bool) -> None:
    """Clear entire cache."""
    if not yes:
        cached = list_cached()
        if not cached:
            click.echo("Cache is already empty.")
            return
        click.echo(f"This will remove {len(cached)} cached dossier(s).")
        if not click.confirm("Continue?"):
            click.echo("Aborted.")
            return

    count = clear_cache()
    click.echo(f"Removed {count} cached dossier(s).")


def _clean_older_than(days: int, yes: bool) -> None:
    """Clean dossiers by age."""
    if not yes:
        click.echo(f"This will remove dossiers cached more than {days} days ago.")
        if not click.confirm("Continue?"):
            click.echo("Aborted.")
            return

    count = delete_older_than(days)
    click.echo(f"Removed {count} cached dossier(s).")


def _clean_specific(name: str, version: str | None) -> None:
    """Clean specific dossier."""
    count = delete_cached(name, version)
    if count == 0:
        target = f"{name}@{version}" if version else name
        click.echo(f"Not cached: {target}")
    elif version:
        click.echo(f"Removed {name}@{version} from cache.")
    else:
        click.echo(f"Removed {count} version(s) of {name} from cache.")


def _show_clean_help() -> None:
    """Show help when no options provided."""
    cached = list_cached()
    if not cached:
        click.echo("Cache is empty.")
    else:
        click.echo(f"Cache contains {len(cached)} dossier(s).")
        click.echo()
        click.echo("To clean the cache, use one of:")
        click.echo("  dossier cache clean <name>          # Remove specific dossier")
        click.echo("  dossier cache clean --older-than N  # Remove entries older than N days")
        click.echo("  dossier cache clean --all           # Remove everything")


@cache.command("clean")
@click.argument("name", required=False)
@click.option("--version", help="Specific version to remove")
@click.option("--older-than", type=int, help="Remove entries older than N days")
@click.option("--all", "clean_all", is_flag=True, help="Remove all cached dossiers")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt")
def cache_clean(
    name: str | None,
    version: str | None,
    older_than: int | None,
    clean_all: bool,
    yes: bool,
) -> None:
    """Remove cached dossiers.

    \b
    Examples:
        dossier cache clean                     # Interactive: shows what would be cleaned
        dossier cache clean myorg/deploy        # Remove all versions of a dossier
        dossier cache clean myorg/deploy --version 1.0.0  # Remove specific version
        dossier cache clean --older-than 30     # Remove entries older than 30 days
        dossier cache clean --all               # Remove everything
    """
    # Validate options
    if version and not name:
        click.echo("Error: --version requires a dossier name", err=True)
        sys.exit(1)

    if clean_all and (name or older_than):
        click.echo("Error: --all cannot be combined with other options", err=True)
        sys.exit(1)

    try:
        if clean_all:
            _clean_all(yes)
        elif older_than is not None:
            _clean_older_than(older_than, yes)
        elif name:
            _clean_specific(name, version)
        else:
            _show_clean_help()
    except CacheError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
