# What is a Dossier?

A **Dossier** is a structured instruction file (`.ds.md`) that AI agents can execute. Instead of writing brittle scripts that try to handle every edge case, dossiers provide clear instructions that LLMs can follow intelligently—adapting to your specific project context.

## The Core Idea

Modern developers already use LLMs in their workflows. So why write complex shell scripts when you can provide structured guidance for intelligent agents?

**Traditional Approach** (brittle):
```bash
# Complex script with 200+ lines
# Must handle: all project types, all edge cases, all errors
# Breaks when encountering unexpected setup
./setup-wizard.sh
```

**Dossier Approach** (adaptive):
```markdown
# Clear instructions for intelligent agent
# Agent adapts to actual project context
# Handles edge cases naturally through understanding
```

## Anatomy of a Dossier

A dossier has two parts:

### 1. Frontmatter (Metadata)

YAML metadata that tools can validate and verify:

```yaml
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
  hash: a3b5c8d9e1f2...
signature:  # Optional
  algorithm: ed25519
  public_key: RWT...
  signed_by: alice@example.com
---
```

### 2. Body (Instructions)

Markdown content that describes what the agent should do:

```markdown
# Setup Development Environment

## Objective
Configure a complete development environment with linting, testing, and git hooks.

## Context to Gather
Before starting, analyze:
- Project type (package.json, pyproject.toml, Cargo.toml, etc.)
- Existing tooling configuration
- CI/CD setup if present

## Steps
1. Detect project type and language
2. Install appropriate dev dependencies
3. Configure linters (ESLint, Ruff, etc.)
4. Set up pre-commit hooks
5. Verify everything works

## Validation
- [ ] Linters run without errors
- [ ] Tests pass
- [ ] Pre-commit hooks are installed and working
```

## When to Use Dossiers

### Use Dossiers When:
- ✅ **Context awareness needed** — detect project structure, adapt to setup
- ✅ **Decisions required** — choose between options based on what exists
- ✅ **Edge cases expected** — handle unexpected configurations gracefully
- ✅ **User guidance helpful** — explain what's happening and why

### Use Scripts When:
- ✅ **Inputs are deterministic** — same input, same output
- ✅ **Speed matters** — millisecond execution required
- ✅ **No decisions needed** — purely mechanical operations
- ✅ **Offline required** — no network access to LLMs

### Examples

| Task | Best Approach | Why |
|------|---------------|-----|
| Set environment variable | Script | Simple, deterministic |
| **Initialize new project** | **Dossier** | Needs to understand project context |
| Run test suite | Script | Fixed commands |
| **Set up development env** | **Dossier** | Detect existing tools, adapt |
| Copy files | Script | Mechanical operation |
| **Review code architecture** | **Dossier** | Requires understanding |

## Dossiers vs AGENTS.md

Many projects use `AGENTS.md` or `.cursorrules` for AI context. Here's how they differ:

|  | AGENTS.md | Dossier |
|--|-----------|---------|
| **Purpose** | Project context & conventions | Executable workflow automation |
| **Scope** | Project-specific | Cross-project, shareable |
| **Validation** | None | Built-in success criteria |
| **Security** | None | Checksums + cryptographic signatures |
| **Tooling** | None | CLI verification, registry |
| **Versioning** | Informal | Semantic versioning |

**They're complementary**: Use AGENTS.md to explain *your project*, use dossiers to automate *workflows*.

## Security & Verification

Dossiers include security features because they contain executable instructions:

### Checksums (Required)
Every dossier includes a SHA256 checksum of its body content. This ensures the instructions haven't been modified:

```yaml
checksum:
  algorithm: sha256
  hash: a3b5c8d9e1f2...
```

Verify with: `dossier verify workflow.ds.md`

### Signatures (Optional)
Dossiers can be cryptographically signed to verify authorship:

```yaml
signature:
  algorithm: ed25519
  public_key: RWT...
  signed_by: alice@example.com
  timestamp: "2025-01-15T10:30:00Z"
```

Sign with: `dossier sign workflow.ds.md --signed-by alice@example.com`

### Trust Levels
- ✅ **VERIFIED**: Signed by a key you trust
- ⚠️ **SIGNED_UNKNOWN**: Valid signature, unknown signer
- ⚠️ **UNSIGNED**: No signature (checksum still verified)
- ❌ **INVALID**: Checksum or signature failed

## Running Dossiers

### With Claude Code (Recommended)

```bash
# Run from registry
dossier run myorg/setup-dev

# Run local file
claude "Execute this dossier:" < workflow.ds.md
```

### With Any LLM

Copy the dossier content into any LLM chat (ChatGPT, Claude.ai, Gemini):

```
This is a dossier—a structured workflow for AI agents.
Please execute it step-by-step and validate the success criteria.

[paste dossier content]
```

## Example Dossiers

### Project Setup
```markdown
---
title: Initialize Node.js Project
objective: Set up a new Node.js project with best practices
---

# Initialize Node.js Project

## Steps
1. Create package.json with appropriate defaults
2. Set up TypeScript if tsconfig.json doesn't exist
3. Configure ESLint and Prettier
4. Add .gitignore
5. Initialize git repository

## Validation
- package.json exists and is valid JSON
- npm install succeeds
- npm run lint passes
```

### Code Review
```markdown
---
title: README Reality Check
objective: Compare README claims against actual implementation
---

# README Reality Check

## Steps
1. Read the README.md
2. Extract all claims about features, installation, and usage
3. Verify each claim against actual code
4. Report discrepancies with file:line references

## Output Format
For each claim, report:
- ✅ Verified: [claim] — [evidence]
- ❌ Unverified: [claim] — [what's actually true]
```

### DevOps
```markdown
---
title: Deploy to Staging
objective: Deploy current branch to staging environment
risk_level: medium
---

# Deploy to Staging

## Prerequisites
- AWS credentials configured
- Docker installed
- Staging cluster accessible

## Steps
1. Run tests to ensure build is stable
2. Build Docker image with current commit SHA
3. Push to ECR
4. Update ECS task definition
5. Deploy and wait for healthy state

## Validation
- Health check endpoint returns 200
- Logs show successful startup
- No error rate spike in monitoring
```

## Learn More

- [CLI Reference](./cli.md) — All commands and options
- [Schema Reference](./schema.md) — Complete frontmatter specification
- [Signing Guide](./signing.md) — Key management and verification
- [Dossier Protocol](https://github.com/imboard-ai/dossier) — Full specification
