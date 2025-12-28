"""CLI for dossier-tools."""

from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any

import click

from ..logging import configure_logging

# Command categories for help organization
COMMAND_SECTIONS: dict[str, list[str]] = OrderedDict(
    [
        ("Local Commands", ["init", "generate-keys", "from-file", "validate", "checksum", "sign", "verify", "info"]),
        (
            "Registry Commands",
            [
                "list",
                "search",
                "get",
                "pull",
                "export",
                "publish",
                "remove",
                "install-skill",
                "login",
                "logout",
                "whoami",
            ],
        ),
        ("Cache Commands", ["cache"]),
        ("Execution Commands", ["run", "new"]),
    ]
)


class SectionedGroup(click.Group):
    """A Click group that organizes commands into sections in help output."""

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Write all commands organized by section."""
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None or cmd.hidden:
                continue
            commands.append((subcommand, cmd))

        if not commands:
            return

        # Build a lookup for quick access
        cmd_lookup = dict(commands)

        for section, cmd_names in COMMAND_SECTIONS.items():
            section_commands = []
            for name in cmd_names:
                if name in cmd_lookup:
                    cmd = cmd_lookup[name]
                    help_text = cmd.get_short_help_str(limit=formatter.width)
                    section_commands.append((name, help_text))

            if section_commands:
                with formatter.section(section):
                    formatter.write_dl(section_commands)


@click.group(cls=SectionedGroup)
@click.version_option()
def main() -> None:
    """Dossier tools for validating, signing, and verifying .ds.md files."""
    configure_logging()


def _format_authors(authors: Any) -> str:
    """Format authors list for display."""
    if not isinstance(authors, list):
        return str(authors)
    author_names = []
    for author in authors:
        if isinstance(author, dict):
            author_names.append(author.get("name", str(author)))
        else:
            author_names.append(str(author))
    return ", ".join(author_names)


def _format_checksum(cs: Any) -> str:
    """Format checksum for display."""
    if isinstance(cs, dict):
        return f"{cs.get('algorithm', 'unknown')}:{cs.get('hash', 'unknown')[:16]}..."
    return str(cs)


def _display_signature(sig: Any) -> None:
    """Display signature info."""
    if isinstance(sig, dict):
        click.echo(f"Signed by: {sig.get('signed_by', 'unknown')}")
        if "timestamp" in sig:
            click.echo(f"Signed at: {sig['timestamp']}")


def display_metadata(fm: dict[str, Any], source: str, as_json: bool) -> None:
    """Display frontmatter metadata."""
    if as_json:
        click.echo(json.dumps(fm, default=str))
        return

    click.echo(f"Source: {source}")
    click.echo()

    # Core fields
    fields = [
        ("name", "Name"),
        ("title", "Title"),
        ("version", "Version"),
        ("status", "Status"),
        ("objective", "Objective"),
    ]
    for key, label in fields:
        if key in fm:
            click.echo(f"{label + ':':<11}{fm[key]}")

    # Authors
    if "authors" in fm:
        click.echo(f"{'Authors:':<11}{_format_authors(fm['authors'])}")

    # Checksum
    if "checksum" in fm:
        click.echo(f"{'Checksum:':<11}{_format_checksum(fm['checksum'])}")

    # Signature
    if "signature" in fm:
        _display_signature(fm["signature"])


# Import and register commands from submodules
from . import cache, local, registry  # noqa: E402, F401
