# Contributing

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

## Development Setup

```bash
# Fork the repo on GitHub first, then clone your fork
git clone https://github.com/YOUR_USERNAME/dossier-tools.git
cd dossier-tools

# Install dependencies
make setup

# Install pre-commit hooks
uv run pre-commit install

# Run tests
make test

# Run linter
make check
```

## Commands

```bash
make verify   # Check Python 3.10+ and uv installed
make setup    # Verify environment + install dependencies
make test     # Run pytest
make coverage # Run pytest with coverage report
make check    # Run ruff format --check && ruff check
make format   # Run ruff format && ruff check --fix
make build    # Build package
```

## Code Architecture

```
src/dossier_tools/
├── __init__.py          # Public API exports
├── cli.py               # Click CLI commands
├── core/
│   ├── parser.py        # Parse .ds.md files (frontmatter + body)
│   ├── validate.py      # JSON Schema validation
│   └── checksum.py      # SHA256 checksum calculation
├── signing/
│   ├── base.py          # Signer/Verifier base classes
│   ├── ed25519.py       # Ed25519 implementation
│   ├── keys.py          # Key storage (~/.dossier/)
│   └── registry.py      # Routes to correct verifier by algorithm
└── registry/
    ├── client.py        # HTTP client for registry API
    ├── auth.py          # Token storage
    └── oauth.py         # GitHub OAuth flow
```

### Module Responsibilities

**`core/`** — Parsing and validation (no crypto)
- `parser.py`: Extracts frontmatter dict and body string from `.ds.md` files
- `validate.py`: Validates frontmatter against `schema/dossier-schema.json`
- `checksum.py`: SHA256 of body content

**`signing/`** — Cryptographic operations
- `base.py`: Abstract `Signer` and `Verifier` classes
- `ed25519.py`: Ed25519 implementation using `cryptography` library
- `keys.py`: Load/save keys from `~/.dossier/`
- `registry.py`: Dispatches verification to correct algorithm handler

**`registry/`** — Remote registry interaction
- `client.py`: HTTP client (httpx) for list/get/pull/publish
- `auth.py`: Credentials storage
- `oauth.py`: GitHub OAuth device flow

### Adding a CLI Command

1. Add function in `cli.py` with `@main.command()` decorator
2. Add to `COMMAND_SECTIONS` dict for help grouping
3. Add tests in `tests/test_cli.py`

```python
@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def mycommand(file: Path) -> None:
    """Short description for help text."""
    # Implementation
    click.echo(f"Processing {file}")
```

### Adding a New Signer

1. Create `signing/mysigner.py`
2. Implement `Signer` and `Verifier` from `base.py`
3. Register in `signing/registry.py`
4. Add tests in `tests/test_signing.py`

```python
from .base import Signer, Verifier, SignatureInfo

class MySigner(Signer):
    def sign(self, content: str, signed_by: str, key_id: str | None = None) -> SignatureInfo:
        # Return SignatureInfo with algorithm, signature, public_key, etc.
        ...

class MyVerifier(Verifier):
    def verify(self, content: str, signature_info: dict) -> SignatureVerificationResult:
        # Return SignatureVerificationResult with status
        ...
```

## Testing

Tests use pytest with fixtures in `tests/fixtures/`.

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_parser.py -v

# Run specific test
uv run pytest tests/test_parser.py::TestParseContent::test_parse_yaml_frontmatter -v
```

### Test Structure

- `tests/fixtures/valid/` — Valid `.ds.md` files
- `tests/fixtures/invalid/` — Invalid files for error testing
- Tests are class-based, grouped by functionality

### Writing Tests

```python
class TestMyFeature:
    """Tests for my feature."""

    def test_happy_path(self):
        """Should do X when Y."""
        result = my_function(valid_input)
        assert result.success

    def test_error_case(self):
        """Should raise Z when invalid."""
        with pytest.raises(MyError, match="expected message"):
            my_function(invalid_input)
```

## Pull Request Guidelines

1. **One feature per PR** — Keep changes focused
2. **Add tests** — New code needs tests
3. **Update docs** — If you change CLI or API, update `docs/`
4. **Run checks** — `make check && make test` must pass
5. **Clear commits** — Write descriptive commit messages

## Error Handling

This project uses two patterns for error handling:

**Result objects** — For validation/verification where failure is an expected outcome:
- `ValidationResult` — Schema validation (valid/invalid)
- `ChecksumResult` — Checksum verification (match/mismatch)
- `SignatureVerificationResult` — Signature verification (valid/invalid/unsigned)

```python
result = validate_frontmatter(data)
if not result.valid:
    print(result.errors)
```

**Exceptions** — For operations where failure is unexpected:
- `ParseError` — File parsing failed (malformed input)
- `RegistryError` — Network/API errors
- `OAuthError` — Authentication flow errors

```python
try:
    parsed = parse_file(path)
except ParseError as e:
    print(f"Failed to parse: {e}")
```

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

- Line length: 120
- Quote style: double
- Import sorting: isort-compatible

Pre-commit hooks run automatically if installed (`uv run pre-commit install`).

## Troubleshooting

**`make setup` fails with "uv not found"**
Install uv: https://docs.astral.sh/uv/

**`make setup` fails with "Python 3.10+ required"**
Install Python 3.10+ via pyenv or your package manager.

**Tests fail with import errors after pulling changes**
Re-run `make setup` to reinstall dependencies.

**Pre-commit hooks fail**
Run `make format` to auto-fix formatting issues.

## Questions?

Open an issue for questions or discussion.
