# CLI Reference

## Commands

### `dossier init`

Initialize the dossier directory.

```bash
dossier init
```

Creates `~/.dossier/` for storing keys.

---

### `dossier generate-keys`

Generate an Ed25519 key pair.

```bash
dossier generate-keys [--name NAME] [--force]
```

| Option | Description |
|--------|-------------|
| `--name NAME` | Key name (default: "default") |
| `--force` | Overwrite existing keys |

Creates:
- `~/.dossier/<name>.pem` — Private key
- `~/.dossier/<name>.pub` — Public key (for sharing)

---

### `dossier create`

Create a dossier from a text file.

```bash
dossier create INPUT [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--title TEXT` | Dossier title (required) |
| `--objective TEXT` | Objective description (required) |
| `--author TEXT` | Author name/email (required, repeatable) |
| `--version TEXT` | Version (default: "1.0.0") |
| `--status TEXT` | Status (default: "draft") |
| `--meta FILE` | JSON file with additional frontmatter |
| `-o, --output FILE` | Output file (default: INPUT.ds.md) |
| `--sign` | Sign after creation |
| `--key NAME` | Key name for signing (default: "default") |
| `--signed-by TEXT` | Signer identity (required with --sign) |

Example:

```bash
dossier create workflow.md \
  --title "Deploy to Production" \
  --objective "Deploy the application" \
  --author "alice@example.com" \
  --sign --signed-by "alice@example.com"
```

---

### `dossier validate`

Validate frontmatter against the schema.

```bash
dossier validate FILE [--json]
```

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |

Exit codes:
- `0` — Valid
- `1` — Invalid

---

### `dossier checksum`

Verify or update the body checksum.

```bash
dossier checksum FILE [--update] [--json]
```

| Option | Description |
|--------|-------------|
| `--update` | Recalculate and update checksum in-place |
| `--json` | Output as JSON |

---

### `dossier sign`

Sign a dossier with Ed25519.

```bash
dossier sign FILE --signed-by IDENTITY [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--signed-by TEXT` | Signer identity (required) |
| `--key NAME` | Key name in ~/.dossier/ (default: "default") |
| `--key-file PATH` | Path to PEM key file |
| `-o, --output FILE` | Output file (default: modify in-place) |

Example:

```bash
dossier sign workflow.ds.md --signed-by "alice@example.com"
```

---

### `dossier verify`

Verify schema, checksum, and signature.

```bash
dossier verify FILE [--json]
```

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |

Output:

```
File: workflow.ds.md

Schema:    valid
Checksum:  valid
Signature: valid (signed by: alice@example.com)
```

---

### `dossier info`

Display local dossier metadata.

```bash
dossier info FILE [--json]
```

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |

Output:

```
Source: workflow.ds.md

Title:     Deploy to Production
Version:   1.0.0
Status:    stable
Objective: Deploy the application
Authors:   Alice
Checksum:  sha256:a3b5c8d9...
Signed by: alice@example.com
```

---

## Registry Commands

These commands interact with a dossier registry. By default, they connect to `https://dossier-registry-mvp.vercel.app`.

To use a different registry, set the `DOSSIER_REGISTRY_URL` environment variable:

```bash
export DOSSIER_REGISTRY_URL=https://registry.example.com
```

---

### `dossier list`

List dossiers from the registry.

```bash
dossier list [--category CATEGORY] [--json]
```

| Option | Description |
|--------|-------------|
| `--category TEXT` | Filter by category |
| `--json` | Output as JSON |

Example:

```bash
dossier list --category devops
```

---

### `dossier get`

Get dossier metadata from the registry.

```bash
dossier get NAME[@VERSION] [--json]
```

| Argument | Description |
|----------|-------------|
| `NAME` | Dossier name (e.g., `myorg/deploy`) |
| `@VERSION` | Optional version suffix (e.g., `myorg/deploy@1.0.0`) |

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |

Example:

```bash
dossier get myorg/deploy@1.0.0
```

---

### `dossier pull`

Download a dossier from the registry.

```bash
dossier pull NAME[@VERSION] [-o OUTPUT]
```

| Argument | Description |
|----------|-------------|
| `NAME` | Dossier name (e.g., `myorg/deploy`) |
| `@VERSION` | Optional version suffix |

| Option | Description |
|--------|-------------|
| `-o, --output FILE` | Output file (default: stdout) |

Example:

```bash
dossier pull myorg/deploy@1.0.0 -o deploy.ds.md
```

---

### `dossier login`

Authenticate with the registry via GitHub OAuth.

```bash
dossier login
```

Opens a browser window for GitHub authentication. After successful authentication, the access token is saved to `~/.dossier/token`.

---

### `dossier logout`

Remove saved authentication token.

```bash
dossier logout
```

Deletes the token file at `~/.dossier/token`.

---

### `dossier whoami`

Show current authenticated user.

```bash
dossier whoami
```

Output:

```
Logged in as: alice
Email:        alice@example.com
```

Exit codes:
- `0` — Logged in
- `1` — Not logged in or token expired

---

### `dossier publish`

Publish a dossier to the registry.

```bash
dossier publish FILE --namespace NAMESPACE [--changelog TEXT]
```

| Option | Description |
|--------|-------------|
| `--namespace TEXT` | Target namespace (required, e.g., `myuser/tools`) |
| `--changelog TEXT` | Changelog message for this version |

Requirements:
- Must be logged in (run `dossier login` first)
- Dossier must pass schema validation
- Dossier checksum must be valid
- You must have permission to publish to the namespace

Example:

```bash
dossier publish deploy.ds.md --namespace alice/devops --changelog "Added rollback support"
```
