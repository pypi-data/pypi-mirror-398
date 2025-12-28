# Schema Reference

Dossier files use YAML frontmatter delimited by `---`. This document describes all fields.

## Required Fields

### `schema_version`

Schema version. Must be `"1.0.0"`.

```yaml
schema_version: "1.0.0"
```

### `title`

Human-readable title. 3-200 characters.

```yaml
title: "Deploy to Production"
```

### `version`

Semantic version of this dossier. Supports prerelease and build metadata.

```yaml
version: "1.0.0"
version: "2.0.0-beta.1"
version: "1.0.0+build.123"
```

### `status`

Lifecycle status. One of:

| Value | Description |
|-------|-------------|
| `draft` | Work in progress |
| `stable` | Production ready |
| `deprecated` | Should not be used |
| `experimental` | Testing new approaches |

```yaml
status: stable
```

### `objective`

What this dossier accomplishes. 10-500 characters.

```yaml
objective: "Deploy the application to production with zero-downtime rolling updates"
```

### `authors`

List of authors. Each author requires `name`, optionally `email` and `url`.

```yaml
authors:
  - name: Alice
    email: alice@example.com
  - name: Bob
```

### `checksum`

SHA256 hash of the body content (everything after the frontmatter).

```yaml
checksum:
  algorithm: sha256
  hash: a3b5c8d9e1f2a3b5c8d9e1f2a3b5c8d9e1f2a3b5c8d9e1f2a3b5c8d9e1f2a3b5
```

The hash is calculated over the body content only, not the frontmatter. Use `dossier checksum --update` to recalculate.

---

## Optional Fields

### `signature`

Cryptographic signature. Added by `dossier sign`.

**Ed25519 signature:**

```yaml
signature:
  algorithm: ed25519
  public_key: "base64-encoded-public-key"
  signature: "base64-encoded-signature"
  signed_by: alice@example.com
  key_id: default
  timestamp: "2024-01-15T10:30:00Z"
```

**AWS KMS signature:**

```yaml
signature:
  algorithm: ecdsa-sha256
  key_id: "alias/dossier-official-prod"
  public_key: "base64-encoded-der-public-key"
  signature: "base64-encoded-der-signature"
  signed_by: "Official <security@example.com>"
  timestamp: "2024-01-15T10:30:00Z"
```

### `category`

List of categories for organization. Common values:

- `devops`, `deployment`, `infrastructure`
- `security`, `testing`, `development`
- `database`, `monitoring`, `ci-cd`
- `migration`, `backup`, `maintenance`

```yaml
category:
  - devops
  - deployment
```

### `tags`

Free-form tags for search.

```yaml
tags:
  - aws
  - kubernetes
  - production
```

### `risk_level`

Risk assessment. One of: `low`, `medium`, `high`, `critical`.

```yaml
risk_level: high
```

### `risk_factors`

Specific risks involved. Common values:

- `modifies_files`, `deletes_files`
- `modifies_cloud_resources`
- `requires_credentials`
- `network_access`
- `executes_external_code`
- `database_operations`
- `system_configuration`

```yaml
risk_factors:
  - modifies_cloud_resources
  - requires_credentials
```

### `requires_approval`

Whether user approval is required before execution. Defaults to `true`.

```yaml
requires_approval: true
```

### `destructive_operations`

Human-readable descriptions of potentially destructive operations.

```yaml
destructive_operations:
  - "Terminates existing EC2 instances"
  - "Drops and recreates database tables"
```

### `estimated_duration`

Estimated execution time in minutes.

```yaml
estimated_duration:
  min_minutes: 5
  max_minutes: 30
```

### `last_updated`

ISO 8601 date of last update.

```yaml
last_updated: "2024-01-15"
```

### `license`

SPDX license identifier.

```yaml
license: MIT
```

### `homepage`

URL to documentation or project page.

```yaml
homepage: "https://github.com/example/dossier-deploy"
```

### `custom`

Arbitrary custom metadata.

```yaml
custom:
  internal_id: "DOSSIER-123"
  team: platform
```

---

## Full Example

```yaml
---
schema_version: "1.0.0"
title: "Deploy to Production"
version: "1.2.0"
status: stable
objective: "Deploy the application to production with zero-downtime rolling updates"
authors:
  - name: Alice
    email: alice@example.com
category:
  - devops
  - deployment
tags:
  - aws
  - kubernetes
risk_level: high
risk_factors:
  - modifies_cloud_resources
  - requires_credentials
requires_approval: true
destructive_operations:
  - "Terminates old deployment pods"
estimated_duration:
  min_minutes: 5
  max_minutes: 15
checksum:
  algorithm: sha256
  hash: a3b5c8d9e1f2a3b5c8d9e1f2a3b5c8d9e1f2a3b5c8d9e1f2a3b5c8d9e1f2a3b5
signature:
  algorithm: ed25519
  public_key: "RWTBase64PublicKey..."
  signature: "Base64Signature..."
  signed_by: alice@example.com
  timestamp: "2024-01-15T10:30:00Z"
---

# Deploy to Production

Your markdown content here...
```

---

## JSON Schema

The full JSON Schema is at [`schema/dossier-schema.json`](../schema/dossier-schema.json).

Validate programmatically:

```python
from dossier_tools import validate_frontmatter

result = validate_frontmatter(frontmatter_dict)
if not result.valid:
    print(result.errors)
```
