# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

dossier-tools is a Python library for validating and signing Dossier workflow files (`.ds.md`). It handles:
- **Schema validation** of frontmatter (JSON Schema)
- **Checksum** verification (SHA256 of body content)
- **Cryptographic signing** (Ed25519, AWS KMS)
- **CLI** for validate/sign/verify operations

**Scope**: Frontmatter + content integrity only. This tool does NOT define or enforce markdown body structure.

## Commands

```bash
make setup    # Install dependencies (uv sync --extra dev)
make test     # Run pytest
make lint     # Run ruff check
make format   # Run ruff format + fix
```

Run a single test:
```bash
uv run pytest tests/test_parser.py -v
uv run pytest tests/test_parser.py::test_specific_function -v
```

## Architecture

```
src/dossier_tools/
├── cli.py              # CLI entry point
├── core/
│   ├── parser.py       # Parse .ds.md files (YAML/JSON frontmatter)
│   ├── validate.py     # Schema validation against JSON schema
│   └── checksum.py     # SHA256 checksum calculation/verification
├── signing/
│   ├── base.py         # Base classes (Signer, Verifier)
│   ├── ed25519.py      # Ed25519 signer/verifier
│   ├── keys.py         # Key management (~/.dossier/)
│   └── registry.py     # Routes verification to correct algorithm
└── registry/
    ├── client.py       # HTTP client for registry API
    ├── auth.py         # Token storage
    └── oauth.py        # OAuth flow for login

schema/
└── dossier-schema.json  # JSON Schema for frontmatter validation
```

## CLI Commands

**Local:** `init`, `generate-keys`, `create`, `validate`, `checksum`, `sign`, `verify`, `info`

**Registry:** `list`, `get`, `pull`, `publish`, `login`, `logout`, `whoami`

## Key Design Decisions

- **Frontmatter format**: Standard `---` delimiter only (YAML/JSON via python-frontmatter)
- **Schema field naming**: `schema_version` (not `dossier_schema_version`)
- **Required fields**: `schema_version`, `title`, `version`, `status`, `objective`, `checksum`, `authors`
- **Optional fields**: `signature`, `risk_level`, `requires_approval`, etc.
- **Default registry**: `https://dossier-registry-mvp.vercel.app` (override with `DOSSIER_REGISTRY_URL`)
- **Auth flow**: Copy/paste OAuth (no local HTTP server) - credentials stored in `~/.dossier/credentials`

## Related Projects

- `/Users/tal/src/dossier2` - Original JS implementation (reference for porting)
- `/Users/tal/src/dossier` - Python project with workflow files and MCP server

## Git Commit Rules

Do not add the following to commit messages:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```
