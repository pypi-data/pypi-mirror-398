# Signing and Verification

Dossiers support two integrity mechanisms:

1. **Checksum** — SHA256 hash of body content. Detects tampering.
2. **Signature** — Ed25519 cryptographic signature. Proves authorship.

---

## Checksum

The checksum covers only the body (markdown content after frontmatter). It does not include the frontmatter itself.

### Verify

```bash
dossier checksum workflow.ds.md
# Checksum valid: workflow.ds.md
```

### Update

After editing the body content:

```bash
dossier checksum workflow.ds.md --update
# Updated checksum: a3b5c8d9...
```

### How It Works

1. Extract body content (everything after `---` frontmatter delimiter)
2. Compute SHA256 hash
3. Compare against `checksum.hash` in frontmatter

---

## Signing

Signatures use Ed25519. Keys are stored in `~/.dossier/`.

### Generate Keys

```bash
dossier init
dossier generate-keys
# Generated key pair 'default':
#   Private key: ~/.dossier/default.pem
#   Public key:  ~/.dossier/default.pub
```

For multiple keys:

```bash
dossier generate-keys --name work
dossier generate-keys --name personal
```

### Sign a Dossier

```bash
dossier sign workflow.ds.md --signed-by alice@example.com
```

Use a specific key:

```bash
dossier sign workflow.ds.md --key work --signed-by alice@example.com
```

Use an external key file:

```bash
dossier sign workflow.ds.md --key-file /path/to/key.pem --signed-by alice@example.com
```

### What Signing Does

1. Reads the dossier content
2. Ensures checksum is valid (updates if needed)
3. Signs the entire content (frontmatter + body) with Ed25519
4. Adds/updates the `signature` block in frontmatter:

```yaml
signature:
  algorithm: ed25519
  public_key: "RWTBase64PublicKey..."
  signature: "Base64Signature..."
  signed_by: alice@example.com
  key_id: default
  timestamp: "2024-01-15T10:30:00Z"
```

---

## Verification

Verify checks schema, checksum, and signature:

```bash
dossier verify workflow.ds.md
```

Output:

```
File: workflow.ds.md

Schema:    valid
Checksum:  valid
Signature: valid (signed by: alice@example.com)
```

### Verification States

| Schema | Checksum | Signature | Exit Code | Meaning |
|--------|----------|-----------|-----------|---------|
| valid | valid | valid | 0 | Fully verified |
| valid | valid | unsigned | 0 | Valid but not signed |
| valid | invalid | - | 1 | Content modified |
| invalid | - | - | 1 | Bad frontmatter |
| - | - | invalid | 1 | Signature doesn't match |

### JSON Output

```bash
dossier verify workflow.ds.md --json
```

```json
{
  "valid": true,
  "schema": {"valid": true, "errors": []},
  "checksum": {"status": "valid", "valid": true},
  "signature": {
    "status": "valid",
    "valid": true,
    "signed_by": "alice@example.com",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## Key Management

Keys are stored in `~/.dossier/`:

```
~/.dossier/
  default.pem     # Private key (keep secret)
  default.pub     # Public key (share freely)
  work.pem
  work.pub
```

### Share Your Public Key

```bash
cat ~/.dossier/default.pub
# ed25519:RWTBase64PublicKey...
```

Share this with anyone who needs to verify your signatures.

### Verify Someone Else's Dossier

Verification uses the public key embedded in the signature. You don't need to pre-install their key.

```bash
dossier verify their-workflow.ds.md
```

---

## Signing Workflow

### Create and Sign

```bash
# Create dossier with signing in one step
dossier create workflow.md \
  --title "My Workflow" \
  --objective "Do something useful" \
  --author "alice@example.com" \
  --sign --signed-by alice@example.com
```

### Edit and Re-sign

After editing a signed dossier:

```bash
# Edit the file...
vim workflow.ds.md

# Re-sign (updates checksum automatically)
dossier sign workflow.ds.md --signed-by alice@example.com
```

### Publish

```bash
dossier login
dossier publish workflow.ds.md
```

The registry validates the signature before accepting.

---

## Security Notes

### What Signing Proves

- The signer had access to the private key
- The content has not been modified since signing
- The `signed_by` identity was claimed by the signer (not verified against external identity)

### What Signing Does Not Prove

- The signer is who they claim to be (no PKI/CA)
- The content is safe to execute
- The signer is authorized to publish

### Key Security

- **Never share your private key** (`*.pem` files)
- Store private keys securely (encrypted disk, secure backup)
- Use separate keys for separate purposes (work vs personal)
- If a key is compromised, re-sign all dossiers with a new key

### Key Backup and Restore

**Backup your keys** — if you lose your private key, you cannot sign new dossiers or prove authorship of existing ones.

```bash
# Backup entire key directory
cp -r ~/.dossier ~/dossier-keys-backup

# Or backup specific keys
cp ~/.dossier/default.pem ~/secure-backup/
cp ~/.dossier/default.pub ~/secure-backup/
```

**Restore from backup:**

```bash
# Restore entire directory
cp -r ~/dossier-keys-backup ~/.dossier

# Or restore specific keys
cp ~/secure-backup/default.pem ~/.dossier/
cp ~/secure-backup/default.pub ~/.dossier/
chmod 600 ~/.dossier/*.pem  # Ensure private keys are protected
```

**Recommended backup locations:**
- Encrypted USB drive
- Password manager (as secure notes)
- Encrypted cloud storage (e.g., age-encrypted file)

### Trust Model

Dossier uses a trust-on-first-use (TOFU) model:

1. First encounter: You see the public key and decide to trust it
2. Subsequent encounters: Verify signature matches the known key
3. Key change: Treat as suspicious until confirmed

There is no central certificate authority. You decide which signers to trust.
