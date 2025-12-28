# Python API

## Parsing

```python
from dossier_tools import parse_file, parse_content

# Parse from file
parsed = parse_file("workflow.ds.md")
print(parsed.frontmatter)  # dict
print(parsed.body)         # str

# Parse from string
content = open("workflow.ds.md").read()
parsed = parse_content(content)
```

## Validation

```python
from dossier_tools import validate_file, validate_frontmatter

# Validate file
result = validate_file("workflow.ds.md")
if result.valid:
    print("Valid")
else:
    print("Errors:", result.errors)

# Validate frontmatter dict
result = validate_frontmatter({
    "schema_version": "1.0.0",
    "title": "My Workflow",
    "version": "1.0.0",
    "status": "draft",
    "objective": "Do something",
    "authors": [{"name": "Alice"}],
    "checksum": {"algorithm": "sha256", "hash": "..."},
})
```

## Checksum

```python
from dossier_tools import calculate_checksum, verify_dossier_checksum, update_checksum

# Calculate checksum of body content
body = "# My Workflow\n\nContent here..."
hash = calculate_checksum(body)  # SHA256 hex string

# Verify checksum of parsed dossier
parsed = parse_file("workflow.ds.md")
result = verify_dossier_checksum(parsed)
print(result.status)  # ChecksumStatus.VALID, INVALID, or MISSING

# Update checksum in content
content = open("workflow.ds.md").read()
updated = update_checksum(content)
```

## Signing

```python
from dossier_tools import sign_dossier, verify_dossier_signature
from dossier_tools.signing.ed25519 import Ed25519Signer

# Generate a new key pair
signer = Ed25519Signer.generate()
print(signer.get_public_key())      # Base64 public key
print(signer.get_private_key_pem()) # PEM private key

# Load from file
signer = Ed25519Signer.from_pem_file("~/.dossier/default.pem")

# Load from environment variable
signer = Ed25519Signer.from_env("DOSSIER_SIGNING_KEY")

# Sign content
content = open("workflow.ds.md").read()
signed = sign_dossier(content, signer, "alice@example.com")

# Verify signature
result = verify_dossier_signature(signed)
print(result.status)     # SignatureStatus.VALID, INVALID, or UNSIGNED
print(result.signed_by)  # "alice@example.com"
print(result.timestamp)  # datetime
```

## Key Management

```python
from dossier_tools.keys import (
    ensure_dossier_dir,
    save_key_pair,
    load_signer,
    key_exists,
    list_keys,
)
from dossier_tools.signing.ed25519 import Ed25519Signer

# Ensure ~/.dossier exists
ensure_dossier_dir()

# Generate and save a key pair
signer = Ed25519Signer.generate()
save_key_pair(signer, name="mykey")
# Creates ~/.dossier/mykey.pem and ~/.dossier/mykey.pub

# Load a saved key
if key_exists("mykey"):
    signer = load_signer("mykey")

# List available keys
keys = list_keys()  # ["default", "mykey"]
```

## Types

```python
from dossier_tools import (
    # Parser
    ParsedDossier,
    ParseError,

    # Validation
    ValidationResult,

    # Checksum
    ChecksumResult,
    ChecksumStatus,

    # Signing
    SignatureInfo,
    SignatureStatus,
    SignatureVerificationResult,
    Signer,
    Verifier,
)
```
