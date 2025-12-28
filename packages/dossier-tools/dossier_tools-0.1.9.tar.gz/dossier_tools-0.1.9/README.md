# dossier-tools

**CLI and library for validating, signing, and running Dossier workflow files (`.ds.md`).**

## What is a Dossier?

A **Dossier** is a markdown file with structured frontmatter that AI agents can execute. Think of it as a recipe for automation—clear instructions that LLMs like Claude Code can follow intelligently.

**Why use Dossiers instead of scripts?**
- **Adaptive**: LLMs understand context and handle edge cases naturally
- **Portable**: Same dossier works across different projects and environments
- **Verifiable**: Built-in checksums and signatures ensure integrity
- **Human-readable**: Plain markdown that anyone can read and modify

```markdown
---
schema_version: "1.0.0"
title: Setup Development Environment
version: "1.0.0"
status: stable
objective: Configure dev environment with proper tooling
authors:
  - name: Alice
checksum:
  algorithm: sha256
  hash: a3b5c8d9...
---

# Setup Development Environment

## Objective
Configure a development environment with linting, testing, and git hooks.

## Steps
1. Detect project type (Node.js, Python, etc.)
2. Install appropriate dev dependencies
3. Configure pre-commit hooks
4. Verify setup works

## Validation
- All linters pass
- Tests run successfully
- Git hooks are installed
```

📖 **Learn more**: [What is a Dossier?](./docs/what-is-a-dossier.md)

## Installation

```bash
pip install dossier-tools
```

Or with uv:

```bash
uv add dossier-tools
```

## Quick Start

### Run a Dossier from the Registry

```bash
# Run a workflow (starts interactive Claude Code session)
dossier run myorg/setup-dev

# Preview without executing
dossier run myorg/setup-dev --print-only
```

> **Note**: Currently only [Claude Code](https://claude.ai/code) is supported as an execution agent.

### Create a New Dossier

```bash
# Create with AI assistance (interactive)
dossier new

# Or from an existing markdown file
dossier from-file workflow.md \
  --name "my-workflow" \
  --title "My Workflow" \
  --objective "Automate something useful" \
  --author "you"
```

### Sign and Verify

```bash
# Initialize and generate signing keys
dossier init
dossier generate-keys

# Validate and sign
dossier validate workflow.ds.md
dossier sign workflow.ds.md --signed-by "you"
dossier verify workflow.ds.md
```

## Registry

Browse and download dossiers from the public registry:

```bash
# List available dossiers
dossier list

# Get metadata
dossier get myorg/deploy

# Download locally
dossier pull myorg/deploy
```

Publish your own (requires GitHub authentication):

```bash
dossier login
dossier publish workflow.ds.md --namespace myorg/tools
```

## Commands

| Command | Description |
|---------|-------------|
| `new` | Create a new dossier with AI assistance |
| `run` | Pull and execute a dossier with Claude Code |
| `from-file` | Create a dossier from an existing markdown file |
| `validate` | Validate frontmatter schema |
| `checksum` | Verify or update checksum |
| `sign` | Sign a dossier |
| `verify` | Verify checksum and signature |
| `list` | List dossiers from the registry |
| `pull` | Download a dossier |
| `get` | Get dossier metadata |
| `publish` | Publish to the registry |
| `login` / `logout` | Manage authentication |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DOSSIER_REGISTRY_URL` | Registry API URL | `https://dossier-registry-mvp-ten.vercel.app` |
| `DOSSIER_SIGNING_KEY` | Default signing key name | `default` |
| `DOSSIER_LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) | `WARNING` |

## Documentation

- [What is a Dossier?](./docs/what-is-a-dossier.md) — Concept, use cases, and comparisons
- [Skills and Dossiers](./docs/SKILLS-AND-DOSSIERS.md) — Why both matter and how they work together
- [Use Case: Start Issue](./docs/USE-CASE-START-ISSUE.md) — Example skill + dossier workflow
- [Blog: Streamlining Issue Workflow](./docs/blog/streamlining-issue-workflow.md) — Step-by-step tutorial
- [CLI Reference](./docs/cli.md) — All commands and options
- [Python API](./docs/api.md) — Using dossier-tools as a library
- [Schema Reference](./docs/schema.md) — Frontmatter field reference
- [Signing Guide](./docs/signing.md) — Signing and verification workflow

## Development

```bash
git clone https://github.com/liberioai/dossier-tools.git
cd dossier-tools
make setup    # Install dependencies
make test     # Run tests
make format   # Format code
```

## License

MIT
