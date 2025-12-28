"""Local CLI commands for dossier-tools."""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path
from typing import Any

import click
import frontmatter

from ..core import (
    ChecksumStatus,
    ParseError,
    calculate_checksum,
    parse_content,
    parse_file,
    update_checksum,
    validate_file,
    validate_frontmatter,
    verify_checksum,
)
from ..signing import (
    SignatureStatus,
    ensure_dossier_dir,
    key_exists,
    load_signer,
    save_key_pair,
    sign_dossier,
    verify_dossier_signature,
)
from ..signing.ed25519 import Ed25519Signer
from . import display_metadata, main


@main.command()
@click.option("--skip-skills", is_flag=True, help="Skip installing recommended skills")
def init(skip_skills: bool) -> None:
    """Initialize dossier and install recommended Claude Code skills.

    Creates the ~/.dossier directory and optionally installs recommended
    skills for Claude Code integration.

    \b
    Examples:
        dossier init              # Initialize and install skills
        dossier init --skip-skills  # Initialize without skills
    """
    dossier_dir = ensure_dossier_dir()
    click.echo(f"Initialized dossier directory: {dossier_dir}")

    if not skip_skills:
        click.echo()
        _install_recommended_skills()


def _install_recommended_skills() -> None:
    """Install recommended Claude Code skills."""
    from .registry import DISCOVERY_SKILL, DISCOVERY_SKILL_NAME, install_skill  # noqa: PLC0415

    skill_path = Path.home() / ".claude" / "skills" / DISCOVERY_SKILL_NAME / "SKILL.md"

    if skill_path.exists():
        click.echo(f"Skill '{DISCOVERY_SKILL_NAME}' is already installed.")
        return

    click.echo("Installing recommended skills...")
    click.echo()

    ctx = click.get_current_context()
    with contextlib.suppress(SystemExit):
        ctx.invoke(install_skill, name=DISCOVERY_SKILL, force=False)


@main.command("generate-keys")
@click.option("--name", default="default", help="Key name (default: 'default')")
@click.option("--force", is_flag=True, help="Overwrite existing keys")
def generate_keys(name: str, force: bool) -> None:
    """Generate a new Ed25519 key pair."""
    if key_exists(name) and not force:
        click.echo(f"Error: Key '{name}' already exists. Use --force to overwrite.", err=True)
        sys.exit(1)

    signer = Ed25519Signer.generate()
    private_path, public_path = save_key_pair(signer, name)

    click.echo(f"Generated key pair '{name}':")
    click.echo(f"  Private key: {private_path}")
    click.echo(f"  Public key:  {public_path}")
    click.echo()
    click.echo("Public key (for sharing):")
    click.echo(f"  {signer.get_public_key()}")


def _validate_create_frontmatter(fm: dict[str, Any]) -> None:
    """Validate frontmatter for create command, exit on error."""
    required = [("name", "--name"), ("title", "--title"), ("objective", "--objective")]
    for field, flag in required:
        if field not in fm:
            click.echo(f"Error: {flag} is required (or provide in --meta)", err=True)
            sys.exit(1)

    if "authors" not in fm or not fm["authors"]:
        click.echo("Error: --author is required (or provide in --meta)", err=True)
        sys.exit(1)

    for i, author in enumerate(fm["authors"]):
        if isinstance(author, str):
            click.echo(f"Error: authors[{i}] must be an object with 'name', not a string", err=True)
            click.echo('  Example: --meta with {"authors": [{"name": "Alice"}]}', err=True)
            sys.exit(1)
        if isinstance(author, dict) and "name" not in author:
            click.echo(f"Error: authors[{i}] missing required 'name' field", err=True)
            sys.exit(1)


@main.command("from-file")
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output file (default: .ds.md extension)")
@click.option("--meta", type=click.Path(exists=True, path_type=Path), help="JSON file with frontmatter fields")
@click.option("--name", "dossier_name", help="Dossier slug (lowercase, hyphens, e.g., 'my-workflow')")
@click.option("--title", help="Dossier title")
@click.option("--version", "doc_version", default="1.0.0", help="Version (default: 1.0.0)")
@click.option("--status", default="draft", help="Status (default: draft)")
@click.option("--objective", help="Objective description")
@click.option("--author", "authors", multiple=True, help="Author name (can be repeated)")
@click.option("--sign", "do_sign", is_flag=True, help="Sign the dossier after creation")
@click.option("--key", "key_name", default="default", help="Key name for signing (default: 'default')")
@click.option("--signed-by", help="Signer identity (required if --sign)")
def from_file(
    input_file: Path,
    output: Path | None,
    meta: Path | None,
    dossier_name: str | None,
    title: str | None,
    doc_version: str,
    status: str,
    objective: str | None,
    authors: tuple[str, ...],
    do_sign: bool,
    key_name: str,
    signed_by: str | None,
) -> None:
    """Create a dossier from a text file and metadata."""
    # Read body content
    body = input_file.read_text(encoding="utf-8")

    # Build frontmatter from meta file and/or options
    fm: dict[str, Any] = {}

    if meta:
        fm = json.loads(meta.read_text(encoding="utf-8"))

    # CLI options override meta file
    if dossier_name:
        fm["name"] = dossier_name
    if title:
        fm["title"] = title
    if objective:
        fm["objective"] = objective
    if authors:
        # Convert CLI author strings to objects with 'name'
        fm["authors"] = [{"name": a} for a in authors]

    # Set defaults
    fm.setdefault("schema_version", "1.0.0")
    fm["version"] = doc_version
    fm["status"] = status

    # Validate required fields and authors format
    _validate_create_frontmatter(fm)

    # Build dossier content with placeholder checksum
    # We need to do a round-trip through frontmatter to normalize the body
    # (e.g., trailing newlines may be stripped), then calculate the checksum
    fm["checksum"] = {"algorithm": "sha256", "hash": ""}
    post = frontmatter.Post(body, **fm)
    content = frontmatter.dumps(post)

    # Recalculate checksum after frontmatter normalization
    content = update_checksum(content)

    # Optionally sign
    if do_sign:
        if not signed_by:
            click.echo("Error: --signed-by is required when using --sign", err=True)
            sys.exit(1)
        if not key_exists(key_name):
            click.echo(f"Error: Key '{key_name}' not found. Run 'dossier generate-keys' first.", err=True)
            sys.exit(1)

        # Warn if signed_by doesn't match any author
        author_names = [a["name"] for a in fm.get("authors", []) if isinstance(a, dict)]
        if signed_by not in author_names:
            click.echo(
                f"Warning: --signed-by '{signed_by}' does not match any author. "
                "Note: signed_by is a self-reported label; trust is based on the public key in trusted-keys.txt.",
                err=True,
            )

        signer = load_signer(key_name)
        content = sign_dossier(content, signer, signed_by)

    # Determine output path
    if output is None:
        output = input_file if input_file.name.endswith(".ds.md") else input_file.with_suffix(".ds.md")

    output.write_text(content, encoding="utf-8")
    click.echo(f"Created: {output}")


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def validate(file: Path, as_json: bool) -> None:
    """Validate dossier schema."""
    result = validate_file(file)

    if as_json:
        click.echo(json.dumps({"valid": result.valid, "errors": result.errors}))
    elif result.valid:
        click.echo(f"Valid: {file}")
    else:
        click.echo(f"Invalid: {file}", err=True)
        for error in result.errors:
            click.echo(f"  - {error}", err=True)

    sys.exit(0 if result.valid else 1)


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--update", "do_update", is_flag=True, help="Update checksum in file (default: verify)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def checksum(file: Path, do_update: bool, as_json: bool) -> None:
    """Verify or update dossier checksum."""
    content = file.read_text(encoding="utf-8")

    try:
        parsed = parse_content(content)
    except ParseError as e:
        if as_json:
            click.echo(json.dumps({"error": str(e)}))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if do_update:
        # Calculate and update checksum
        new_hash = calculate_checksum(parsed.body)
        parsed.frontmatter.setdefault("checksum", {})
        parsed.frontmatter["checksum"]["algorithm"] = "sha256"
        parsed.frontmatter["checksum"]["hash"] = new_hash

        post = frontmatter.Post(parsed.body, **parsed.frontmatter)
        file.write_text(frontmatter.dumps(post), encoding="utf-8")

        if as_json:
            click.echo(json.dumps({"updated": True, "hash": new_hash}))
        else:
            click.echo(f"Updated checksum: {new_hash}")
        sys.exit(0)

    # Verify mode
    result = verify_checksum(parsed.body, parsed.frontmatter)

    if as_json:
        click.echo(
            json.dumps(
                {
                    "status": result.status.value,
                    "valid": result.valid,
                    "expected": result.expected,
                    "actual": result.actual,
                }
            )
        )
    elif result.status == ChecksumStatus.VALID:
        click.echo(f"Checksum valid: {file}")
    elif result.status == ChecksumStatus.MISSING:
        click.echo(f"Checksum missing: {file}", err=True)
    else:
        click.echo(f"Checksum invalid: {file}", err=True)
        click.echo(f"  Expected: {result.expected}", err=True)
        click.echo(f"  Actual:   {result.actual}", err=True)

    sys.exit(0 if result.valid else 1)


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--key", "key_name", default="default", help="Key name from ~/.dossier/ (default: 'default')")
@click.option("--key-file", type=click.Path(exists=True, path_type=Path), help="Path to PEM key file")
@click.option("--signed-by", required=True, help="Signer identity (e.g., email). Note: self-reported, not verified.")
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output file (default: modify in place)")
def sign(file: Path, key_name: str, key_file: Path | None, signed_by: str, output: Path | None) -> None:
    """Sign a dossier."""
    # Load signer
    if key_file:
        signer = Ed25519Signer.from_pem_file(key_file)
    else:
        if not key_exists(key_name):
            click.echo(f"Error: Key '{key_name}' not found. Run 'dossier generate-keys' first.", err=True)
            sys.exit(1)
        signer = load_signer(key_name)

    # Read and parse file
    content = file.read_text(encoding="utf-8")
    try:
        parsed = parse_content(content)
    except ParseError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Warn if signed_by doesn't match any author
    author_names = [a["name"] for a in parsed.frontmatter.get("authors", []) if isinstance(a, dict)]
    if signed_by not in author_names:
        click.echo(
            f"Warning: --signed-by '{signed_by}' does not match any author. "
            "Note: signed_by is a self-reported label; trust is based on the public key in trusted-keys.txt.",
            err=True,
        )

    # Sign
    signed_content = sign_dossier(content, signer, signed_by)

    # Write output
    output_path = output or file
    output_path.write_text(signed_content, encoding="utf-8")

    if output:
        click.echo(f"Signed: {file} -> {output}")
    else:
        click.echo(f"Signed: {file}")


def _display_schema_result(schema_result: Any) -> None:
    """Display schema validation result."""
    if schema_result.valid:
        click.echo("Schema:    valid")
    else:
        click.echo("Schema:    invalid", err=True)
        for error in schema_result.errors:
            click.echo(f"  - {error}", err=True)


def _display_checksum_result(checksum_result: Any) -> None:
    """Display checksum verification result."""
    status_display = {
        ChecksumStatus.VALID: ("Checksum:  valid", False),
        ChecksumStatus.MISSING: ("Checksum:  missing", False),
    }
    message, is_error = status_display.get(checksum_result.status, ("Checksum:  invalid", True))
    click.echo(message, err=is_error)


def _display_signature_result(sig_result: Any) -> None:
    """Display signature verification result."""
    if sig_result.status == SignatureStatus.VALID:
        click.echo(f"Signature: valid (signed by: {sig_result.signed_by})")
    elif sig_result.status == SignatureStatus.UNSIGNED:
        click.echo("Signature: unsigned")
    else:
        click.echo(f"Signature: invalid ({sig_result.error})", err=True)


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def verify(file: Path, as_json: bool) -> None:
    """Verify dossier checksum and signature."""
    content = file.read_text(encoding="utf-8")

    try:
        parsed = parse_content(content)
    except ParseError as e:
        if as_json:
            click.echo(json.dumps({"error": str(e)}))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Validate schema
    schema_result = validate_frontmatter(parsed.frontmatter)

    # Verify checksum
    checksum_result = verify_checksum(parsed.body, parsed.frontmatter)

    # Verify signature
    sig_result = verify_dossier_signature(content)

    # Determine overall validity
    all_valid = (
        schema_result.valid
        and checksum_result.valid
        and sig_result.status in (SignatureStatus.VALID, SignatureStatus.UNSIGNED)
    )

    if as_json:
        output_data = {
            "valid": all_valid,
            "schema": {"valid": schema_result.valid, "errors": schema_result.errors},
            "checksum": {
                "status": checksum_result.status.value,
                "valid": checksum_result.valid,
            },
            "signature": {
                "status": sig_result.status.value,
                "valid": sig_result.valid,
                "signed_by": sig_result.signed_by,
                "timestamp": sig_result.timestamp.isoformat() if sig_result.timestamp else None,
            },
        }
        click.echo(json.dumps(output_data))
    else:
        click.echo(f"File: {file}")
        click.echo()
        _display_schema_result(schema_result)
        _display_checksum_result(checksum_result)
        _display_signature_result(sig_result)

    sys.exit(0 if all_valid else 1)


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def info(file: Path, as_json: bool) -> None:
    """Display local dossier metadata."""
    try:
        parsed = parse_file(file)
    except ParseError as e:
        if as_json:
            click.echo(json.dumps({"error": str(e)}))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    display_metadata(parsed.frontmatter, str(file), as_json)
