"""Registry and execution CLI commands for dossier-tools."""

from __future__ import annotations

import getpass
import http
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from ..cache import (
    CacheError,
    cache_dossier,
    get_cached_path,
    get_latest_cached,
    is_cached,
    read_cached,
)
from ..core import (
    ParseError,
    parse_file,
    validate_frontmatter,
    verify_checksum,
)
from ..registry import (
    OAuthError,
    RegistryError,
    delete_credentials,
    get_client,
    get_registry_url,
    load_credentials,
    load_token,
    parse_name_version,
    run_oauth_flow,
)
from . import display_metadata, main

# The dossier-discovery skill to suggest on first run
DISCOVERY_SKILL = "imboard-ai/skills/dossier-discovery"
DISCOVERY_SKILL_NAME = "dossier-discovery"


def _get_dossier_config_dir() -> Path:
    """Get the dossier config directory (~/.dossier/)."""
    return Path.home() / ".dossier"


def _is_discovery_skill_installed() -> bool:
    """Check if the dossier-discovery skill is installed."""
    skill_path = Path.home() / ".claude" / "skills" / DISCOVERY_SKILL_NAME / "SKILL.md"
    return skill_path.exists()


def _get_discovery_prompt_file() -> Path:
    """Get the path to the discovery skill prompt record file."""
    return _get_dossier_config_dir() / "discovery_skill_prompt.json"


def _has_prompted_for_discovery() -> bool:
    """Check if we've already prompted for the discovery skill."""
    prompt_file = _get_discovery_prompt_file()
    return prompt_file.exists()


def _record_discovery_prompt(accepted: bool) -> None:
    """Record the user's response to the discovery skill prompt.

    Args:
        accepted: Whether the user accepted the prompt to install
    """
    config_dir = _get_dossier_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    prompt_record = {
        "skill": DISCOVERY_SKILL,
        "prompt": "Install the 'dossier-discovery' skill for proactive workflow suggestions?",
        "response": "yes" if accepted else "no",
        "user": getpass.getuser(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    prompt_file = _get_discovery_prompt_file()
    prompt_file.write_text(json.dumps(prompt_record, indent=2), encoding="utf-8")


def _prompt_for_discovery_skill() -> None:
    """Prompt user to install the dossier-discovery skill on first run."""
    if _is_discovery_skill_installed() or _has_prompted_for_discovery():
        return

    click.echo()
    click.echo("Tip: Install the 'dossier-discovery' skill for proactive workflow suggestions.")
    click.echo("This skill helps find relevant dossiers when you start complex tasks.")
    click.echo()

    accepted = click.confirm("Install it now?")

    if accepted:
        click.echo()
        # Get the current context and invoke install_skill
        ctx = click.get_current_context()
        ctx.invoke(install_skill, name=DISCOVERY_SKILL, force=False)
    else:
        click.echo("You can install it later with: dossier init")
        click.echo()

    _record_discovery_prompt(accepted)


@main.command("list")
@click.option("--category", help="Filter by category")
@click.option("--url", "show_url", is_flag=True, help="Show content URLs")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_cmd(category: str | None, show_url: bool, as_json: bool) -> None:
    """List dossiers from the registry."""
    registry_url = get_registry_url()

    try:
        with get_client() as client:
            result = client.list_dossiers(category=category)
    except RegistryError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    dossiers = result.get("dossiers", [])

    if as_json:
        # Add URLs to JSON output if requested
        if show_url:
            for d in dossiers:
                name = d.get("name", "")
                d["content_url"] = f"{registry_url}/api/v1/dossiers/{name}/content"
        click.echo(json.dumps(result))
    elif not dossiers:
        click.echo("No dossiers found.")
    elif show_url:
        # Print with URLs
        for d in dossiers:
            name = d.get("name", "")
            version = d.get("version", "")
            title = d.get("title", "")
            url = f"{registry_url}/api/v1/dossiers/{name}/content"
            click.echo(f"{name:30} {version:10} {title}")
            click.echo(f"  {url}")
    else:
        # Print as table
        for d in dossiers:
            name = d.get("name", "")
            version = d.get("version", "")
            title = d.get("title", "")
            click.echo(f"{name:30} {version:10} {title}")


@main.command()
@click.argument("query")
@click.option("-c", "--content", is_flag=True, help="Also search inside dossier content (slower)")
@click.option("--limit", type=int, help="Maximum number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search(query: str, content: bool, limit: int | None, as_json: bool) -> None:
    """Search dossiers by name, title, description, or content.

    Searches dossier metadata (name, title, description, category, tags) by default.
    Use --content to also search inside the dossier markdown body.

    \b
    Examples:
        dossier search react
        dossier search "setup project" --content
        dossier search deploy --limit 5
        dossier search kubernetes --json
    """
    from ..search import search_dossiers  # noqa: PLC0415

    try:
        with get_client() as client:
            results = search_dossiers(
                client=client,
                query=query,
                include_content=content,
                limit=limit,
            )
    except RegistryError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps([r.to_dict() for r in results]))
        return

    if not results:
        click.echo(f'No dossiers found matching "{query}".')
        return

    click.echo(f'Found {len(results)} dossier(s) matching "{query}":')
    click.echo()

    for r in results:
        # Show match type indicator for content matches
        match_indicator = " [content]" if r.match_type == "content" else ""
        click.echo(f"  {r.name} (v{r.version}){match_indicator}")
        click.echo(f"  {r.title}")

        # Show tags if present
        if r.tags:
            click.echo(f"  [{', '.join(r.tags)}]")

        # Show content context if available
        for m in r.matches:
            if m.field == "content" and m.context:
                click.echo(f"  > {m.context}")

        click.echo()


@main.command()
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def get(name: str, as_json: bool) -> None:
    """Get dossier metadata from the registry."""
    dossier_name, version = parse_name_version(name)
    registry_url = get_registry_url()

    try:
        with get_client() as client:
            result = client.get_dossier(dossier_name, version=version)
    except RegistryError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Get resolved version from result
    resolved_version = result.get("version", version)

    if as_json:
        # Add URLs and cache status to JSON output
        result["registry_url"] = registry_url
        result["content_url"] = f"{registry_url}/api/v1/dossiers/{dossier_name}/content"
        if resolved_version and is_cached(dossier_name, resolved_version):
            result["cached"] = str(get_cached_path(dossier_name, resolved_version))
        else:
            result["cached"] = None

    display_metadata(result, f"registry:{dossier_name}", as_json)

    if not as_json:
        # Display additional info
        click.echo()
        click.echo(f"{'Registry:':<11}{registry_url}")
        click.echo(f"{'Content:':<11}{registry_url}/api/v1/dossiers/{dossier_name}/content")

        if resolved_version and is_cached(dossier_name, resolved_version):
            cache_path = get_cached_path(dossier_name, resolved_version)
            click.echo(f"{'Cached:':<11}{cache_path}")
        else:
            click.echo(f"{'Cached:':<11}No")


@main.command()
@click.argument("names", nargs=-1, required=True)
@click.option("--force", is_flag=True, help="Re-download even if cached")
def pull(names: tuple[str, ...], force: bool) -> None:
    """Cache dossiers locally for offline use.

    Downloads dossiers from the registry and caches them in ~/.dossier/cache/.
    Cached dossiers are used by 'dossier run' for faster execution.

    NAMES can include version specifiers: 'myorg/deploy' or 'myorg/deploy@1.0.0'

    \b
    Examples:
        dossier pull myorg/deploy
        dossier pull myorg/deploy@1.0.0
        dossier pull myorg/deploy myorg/backup --force
    """
    registry_url = get_registry_url()

    for name in names:
        dossier_name, version = parse_name_version(name)

        try:
            with get_client() as client:
                # Resolve version if not specified
                if version is None:
                    click.echo(f"Pulling {dossier_name}...")
                    click.echo("  Fetching metadata...", nl=False)
                    metadata = client.get_dossier(dossier_name)
                    version = metadata.get("version", "unknown")
                    click.echo(f" v{version}")
                else:
                    click.echo(f"Pulling {dossier_name}@{version}...")

                # Check if already cached
                if not force and is_cached(dossier_name, version):
                    click.echo(f"{dossier_name}@{version} already cached (use --force to re-download)")
                    continue

                # Download content
                click.echo("  Downloading content...")
                content, _ = client.pull_content(dossier_name, version=version)

                # Cache the content
                source_url = f"{registry_url}/api/v1/dossiers/{dossier_name}/content"
                cache_path = cache_dossier(dossier_name, version, content, source_url)
                click.echo(f"Cached: {cache_path}")

        except RegistryError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except CacheError as e:
            click.echo(f"Cache error: {e}", err=True)
            sys.exit(1)


def _fetch_and_save_dossier(name: str, output: Path, *, verbose: bool = False) -> tuple[str | None, str | None]:
    """Fetch a dossier from registry and save to output path.

    Args:
        name: Dossier name, optionally with @version suffix
        output: Path to write the file to
        verbose: Whether to resolve and print version info (keyword-only)

    Returns:
        Tuple of (resolved_version, digest). Version may be None if not resolved.

    Raises:
        SystemExit on error
    """
    dossier_name, version = parse_name_version(name)

    try:
        with get_client() as client:
            # Only resolve version when verbose - otherwise let server use latest
            if verbose and version is None:
                click.echo(f"Fetching {dossier_name}...")
                metadata = client.get_dossier(dossier_name)
                version = metadata.get("version", "unknown")
                click.echo(f"  Found version: {version}")

            content, digest = client.pull_content(dossier_name, version=version)
    except RegistryError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Create parent directories if needed
    output.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    output.write_text(content, encoding="utf-8")

    return version, digest


@main.command()
@click.argument("name")
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output file path")
@click.option("--stdout", is_flag=True, help="Print to stdout instead of file")
def export(name: str, output: Path | None, stdout: bool) -> None:
    """Export a dossier to a local file.

    Downloads a dossier from the registry and saves it to a file.
    Use this when you want to customize or vendor a dossier.

    NAME can include a version specifier: 'myorg/deploy' or 'myorg/deploy@1.0.0'

    \b
    Examples:
        dossier export myorg/deploy
        dossier export myorg/deploy -o ./workflows/deploy.ds.md
        dossier export myorg/deploy --stdout
    """
    dossier_name, version = parse_name_version(name)

    # Output to stdout - need to fetch directly
    if stdout:
        try:
            with get_client() as client:
                content, _ = client.pull_content(dossier_name, version=version)
        except RegistryError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        click.echo(content)
        return

    # Determine output path
    if output is None:
        filename = dossier_name.replace("/", "-") + ".ds.md"
        output = Path(filename)

    version, digest = _fetch_and_save_dossier(name, output, verbose=False)

    click.echo(f"Exported: {output.resolve()}")
    if digest:
        click.echo(f"Digest: {digest}")


@main.command("install-skill")
@click.argument("name")
@click.option("--force", is_flag=True, help="Overwrite if skill already exists")
def install_skill(name: str, force: bool) -> None:
    """Install a Claude Code skill from the registry.

    Downloads a dossier from the registry and installs it as a Claude Code skill
    at ~/.claude/skills/<skill-name>/SKILL.md.

    NAME can include a version specifier: 'myorg/skill-name' or 'myorg/skill-name@1.0.0'

    \b
    Examples:
        dossier install-skill imboard-ai/skills/start-issue
        dossier install-skill myorg/skills/review-pr@1.0.0
        dossier install-skill myorg/skills/deploy --force
    """
    dossier_name, _ = parse_name_version(name)

    # Extract skill name from dossier name (last part of the path)
    skill_name = dossier_name.split("/")[-1]

    # Target path: ~/.claude/skills/<skill-name>/SKILL.md
    skill_file = Path.home() / ".claude" / "skills" / skill_name / "SKILL.md"

    # Check if skill already exists
    if skill_file.exists() and not force:
        click.echo(f"Skill '{skill_name}' already exists at {skill_file}", err=True)
        click.echo("Use --force to overwrite.", err=True)
        sys.exit(1)

    version, _ = _fetch_and_save_dossier(name, skill_file, verbose=True)

    click.echo()
    version_str = f" (v{version})" if version else ""
    click.echo(f"Installed skill '{skill_name}'{version_str} to:")
    click.echo(f"  {skill_file}")


@main.command()
def login() -> None:
    """Authenticate with the registry via GitHub."""
    registry_url = get_registry_url()

    # Check if already logged in
    creds = load_credentials()
    if creds and not creds.is_expired():
        click.echo(f"Already logged in as {creds.username}")
        if not click.confirm("Login again?"):
            return

    click.echo("Opening browser for GitHub authentication...")

    try:
        result = run_oauth_flow(registry_url)

        # Save credentials
        from ..registry import Credentials, save_credentials  # noqa: PLC0415

        save_credentials(
            Credentials(
                token=result.token,
                username=result.username,
                orgs=result.orgs,
            )
        )

        click.echo(f"Logged in as {result.username}" + (f" ({result.email})" if result.email else ""))
        click.echo("Credentials saved to ~/.dossier/credentials")
    except OAuthError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
def logout() -> None:
    """Remove saved authentication."""
    if delete_credentials():
        click.echo("Logged out successfully.")
    else:
        click.echo("Not logged in.")


@main.command()
def whoami() -> None:
    """Show current authenticated user."""
    creds = load_credentials()
    if not creds:
        click.echo("Not logged in. Run 'dossier login' to authenticate.")
        sys.exit(1)

    if creds.is_expired():
        click.echo("Session expired. Run 'dossier login' to re-authenticate.")
        sys.exit(1)

    click.echo(f"Logged in as: {creds.username}")
    if creds.orgs:
        click.echo(f"Orgs:         {', '.join(creds.orgs)}")


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--namespace", required=True, help="Target namespace (e.g., 'myuser/tools' or 'myorg/category')")
@click.option("--changelog", help="Changelog message for this version")
def publish(file: Path, namespace: str, changelog: str | None) -> None:
    """Publish a dossier to the registry."""
    token = load_token()
    if not token:
        click.echo("Not logged in. Run 'dossier login' first.", err=True)
        sys.exit(1)

    # Parse and validate file
    try:
        dossier = parse_file(file)
    except ParseError as e:
        click.echo(f"Error parsing file: {e}", err=True)
        sys.exit(1)

    # Validate schema
    schema_result = validate_frontmatter(dossier.frontmatter)
    if not schema_result.valid:
        click.echo("Validation errors:", err=True)
        for err in schema_result.errors:
            click.echo(f"  - {err}", err=True)
        sys.exit(1)

    # Verify checksum
    checksum_result = verify_checksum(dossier.body, dossier.frontmatter)
    if not checksum_result.valid:
        click.echo(f"Checksum error: {checksum_result.status.value}", err=True)
        sys.exit(1)

    # Get name from frontmatter for display
    name = dossier.frontmatter.get("name", file.stem)
    version = dossier.frontmatter.get("version", "unknown")

    # Publish
    try:
        with get_client(token=token) as client:
            content = file.read_text(encoding="utf-8")
            result = client.publish(namespace, content, changelog=changelog)
            full_name = result.get("name", f"{namespace}/{name}")
            click.echo(f"Published {full_name}@{version}")
            if "content_url" in result:
                click.echo(f"URL: {result['content_url']}")
            click.echo()
            click.echo("Note: It may take 1-2 minutes for the dossier to appear in 'dossier list'.")
    except RegistryError as e:
        if e.status_code == http.HTTPStatus.UNAUTHORIZED:
            click.echo("Session expired. Run 'dossier login' to re-authenticate.", err=True)
        elif e.status_code == http.HTTPStatus.FORBIDDEN:
            click.echo(f"Permission denied: {e}", err=True)
        elif e.status_code == http.HTTPStatus.CONFLICT:
            click.echo(f"Version conflict: {e}", err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def remove(name: str, yes: bool) -> None:
    """Remove a dossier from the registry.

    NAME can be 'dossier-name' to remove all versions, or 'dossier-name@version'
    to remove a specific version.

    Requires authentication. You must have permission to delete the dossier.
    """
    token = load_token()
    if not token:
        click.echo("Not logged in. Run 'dossier login' first.", err=True)
        sys.exit(1)

    dossier_name, version = parse_name_version(name)
    target = f"{dossier_name}@{version}" if version else dossier_name

    # Confirm deletion
    if not yes:
        if version:
            msg = f"Are you sure you want to remove version '{version}' of '{dossier_name}'?"
        else:
            msg = f"Are you sure you want to remove '{dossier_name}' and ALL its versions?"
        if not click.confirm(msg):
            click.echo("Aborted.")
            return

    try:
        with get_client(token=token) as client:
            client.delete_dossier(dossier_name, version=version)
            click.echo(f"Removed: {target}")
    except RegistryError as e:
        if e.status_code == http.HTTPStatus.UNAUTHORIZED:
            click.echo("Session expired. Run 'dossier login' to re-authenticate.", err=True)
        elif e.status_code == http.HTTPStatus.FORBIDDEN:
            click.echo(f"Permission denied: {e}", err=True)
        elif e.status_code == http.HTTPStatus.NOT_FOUND:
            click.echo(f"Not found: {target}", err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# --- Execution commands ---


def _is_inside_claude_code() -> bool:
    """Check if we're running inside a Claude Code session."""
    return os.environ.get("CLAUDECODE") == "1"


def _get_from_cache(dossier_name: str, version: str | None) -> tuple[str | None, str | None, bool]:
    """Try to get dossier content from cache.

    Returns:
        Tuple of (content, version, from_cache)
    """
    if version and is_cached(dossier_name, version):
        content = read_cached(dossier_name, version)
        if content:
            return content, version, True

    if not version:
        cached = get_latest_cached(dossier_name)
        if cached:
            content = read_cached(dossier_name, cached.version)
            if content:
                click.echo(f"Using cached version {cached.version}")
                return content, cached.version, True

    return None, version, False


def _fetch_from_registry(dossier_name: str, version: str | None, do_cache: bool) -> tuple[str, str]:
    """Fetch dossier content from registry.

    Returns:
        Tuple of (content, version)

    Raises:
        SystemExit on error
    """
    try:
        with get_client() as client:
            if version is None:
                metadata = client.get_dossier(dossier_name)
                version = metadata.get("version", "unknown")

            content, _ = client.pull_content(dossier_name, version=version)

            if do_cache:
                registry_url = get_registry_url()
                source_url = f"{registry_url}/api/v1/dossiers/{dossier_name}/content"
                try:
                    cache_path = cache_dossier(dossier_name, version, content, source_url)
                    click.echo(f"Cached: {cache_path}")
                except CacheError as e:
                    click.echo(f"Warning: Could not cache: {e}", err=True)

            return content, version

    except RegistryError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("name")
@click.option("--no-cache", "no_cache", is_flag=True, help="Skip cache, fetch from registry")
@click.option("--pull", "do_pull", is_flag=True, help="Update cache before running")
@click.option("--print-only", is_flag=True, help="Print the workflow content instead of running it")
def run(name: str, no_cache: bool, do_pull: bool, print_only: bool) -> None:
    """Run a dossier workflow using Claude Code.

    Uses cached dossiers when available. If not cached, fetches from registry.

    If already running inside Claude Code, prints the workflow content for the
    current session to execute instead of spawning a nested session.

    NAME can be 'workflow-name' or 'workflow-name@version'.

    \b
    Examples:
        dossier run myorg/deploy           # Use cache if available
        dossier run myorg/deploy --no-cache  # Always fetch from registry
        dossier run myorg/deploy --pull    # Update cache and run

    Supported agents: Claude Code only (https://claude.ai/code)
    """
    # Prompt to install dossier-discovery skill on first run
    if not print_only:
        _prompt_for_discovery_skill()

    inside_claude = _is_inside_claude_code()
    claude_path = shutil.which("claude")

    if not claude_path and not print_only and not inside_claude:
        click.echo("Error: Claude Code is not installed or not in PATH.", err=True)
        click.echo("To install Claude Code, visit: https://claude.ai/code", err=True)
        sys.exit(1)

    dossier_name, version = parse_name_version(name)
    from_cache = False

    # Get content from cache or registry
    if no_cache or do_pull:
        content, used_version = _fetch_from_registry(dossier_name, version, do_pull)
    else:
        content, used_version, from_cache = _get_from_cache(dossier_name, version)
        if content is None:
            content, used_version = _fetch_from_registry(dossier_name, version, do_cache=False)

    # Output content for print-only or inside Claude Code
    if print_only or inside_claude:
        if inside_claude and not print_only:
            source = "cached" if from_cache else "registry"
            click.echo(f"Running workflow: {dossier_name}@{used_version} ({source})")
            click.echo()
        click.echo(content)
        return

    # Execute with Claude Code
    source = "cached" if from_cache else "registry"
    click.echo(f"Running workflow: {dossier_name}@{used_version} ({source})")
    click.echo("Starting Claude Code...")
    click.echo()

    result = subprocess.run([claude_path, "--", content], check=False)
    sys.exit(result.returncode)


DEFAULT_CREATE_TEMPLATE = "imboard-ai/meta/create-dossier"


@main.command()
@click.option(
    "--template",
    default=DEFAULT_CREATE_TEMPLATE,
    help=f"Template dossier (default: {DEFAULT_CREATE_TEMPLATE})",
)
def new(template: str) -> None:
    """Create a new dossier with AI assistance.

    Pulls a template dossier from the registry and runs it to guide you through
    creating a new dossier from scratch.

    Uses Claude Code to interactively help you write the workflow instructions,
    validation criteria, and metadata.
    """
    # Delegate to run command
    ctx = click.get_current_context()
    ctx.invoke(run, name=template, print_only=False)
