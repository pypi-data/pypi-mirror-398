"""Tests for the CLI."""

import json

import respx
from click.testing import CliRunner
from httpx import Response

from dossier_tools.cli import COMMAND_SECTIONS, main
from dossier_tools.signing import get_dossier_dir, get_private_key_path, get_public_key_path

from .conftest import FIXTURES_DIR

# Test helper for cache metadata
TEST_CACHE_META = json.dumps(
    {
        "cached_at": "2025-01-01T00:00:00Z",
        "version": "1.0.0",
        "source_registry_url": "test",
    }
)


class TestCommandSections:
    """Tests for CLI command organization."""

    def test_all_commands_in_sections(self):
        """All commands should be listed in COMMAND_SECTIONS for help display."""
        # Get all registered commands
        registered_commands = set(main.commands.keys())

        # Get all commands listed in sections
        sectioned_commands = set()
        for cmd_list in COMMAND_SECTIONS.values():
            sectioned_commands.update(cmd_list)

        # Find commands missing from sections
        missing = registered_commands - sectioned_commands
        assert not missing, f"Commands not in COMMAND_SECTIONS: {missing}"

    def test_no_stale_commands_in_sections(self):
        """COMMAND_SECTIONS should not list non-existent commands."""
        registered_commands = set(main.commands.keys())

        sectioned_commands = set()
        for cmd_list in COMMAND_SECTIONS.values():
            sectioned_commands.update(cmd_list)

        # Find stale entries in sections
        stale = sectioned_commands - registered_commands
        assert not stale, f"Stale commands in COMMAND_SECTIONS: {stale}"


class TestInit:
    """Tests for init command."""

    def test_creates_dossier_directory(self, tmp_path, monkeypatch):
        """Should create ~/.dossier directory."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        result = runner.invoke(main, ["init"])

        assert result.exit_code == 0
        assert (tmp_path / ".dossier").is_dir()
        assert "Initialized" in result.output


class TestGenerateKeys:
    """Tests for generate-keys command."""

    def test_generates_key_pair(self, tmp_path, monkeypatch):
        """Should generate key pair in ~/.dossier."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        result = runner.invoke(main, ["generate-keys"])

        assert result.exit_code == 0
        assert (tmp_path / ".dossier" / "default.pem").exists()
        assert (tmp_path / ".dossier" / "default.pub").exists()
        assert "Generated key pair" in result.output

    def test_generates_named_key(self, tmp_path, monkeypatch):
        """Should generate key with custom name."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        result = runner.invoke(main, ["generate-keys", "--name", "mykey"])

        assert result.exit_code == 0
        assert (tmp_path / ".dossier" / "mykey.pem").exists()
        assert (tmp_path / ".dossier" / "mykey.pub").exists()

    def test_fails_if_key_exists(self, tmp_path, monkeypatch):
        """Should fail if key already exists without --force."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Generate first key
        runner.invoke(main, ["generate-keys"])

        # Try to generate again
        result = runner.invoke(main, ["generate-keys"])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_force_overwrites_key(self, tmp_path, monkeypatch):
        """Should overwrite key with --force."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Generate first key
        runner.invoke(main, ["generate-keys"])
        original_pub = (tmp_path / ".dossier" / "default.pub").read_text()

        # Force overwrite
        result = runner.invoke(main, ["generate-keys", "--force"])

        assert result.exit_code == 0
        new_pub = (tmp_path / ".dossier" / "default.pub").read_text()
        assert new_pub != original_pub


class TestCreate:
    """Tests for create command."""

    def test_missing_title(self, tmp_path, monkeypatch):
        """Should error when --title is missing."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        input_file = tmp_path / "input.md"
        input_file.write_text("Body content.")

        result = runner.invoke(
            main,
            ["from-file", str(input_file), "--name", "test", "--objective", "Test", "--author", "test@example.com"],
        )

        assert result.exit_code == 1
        assert "--title is required" in result.output

    def test_missing_objective(self, tmp_path, monkeypatch):
        """Should error when --objective is missing."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        input_file = tmp_path / "input.md"
        input_file.write_text("Body content.")

        result = runner.invoke(
            main,
            ["from-file", str(input_file), "--name", "test", "--title", "Test", "--author", "test@example.com"],
        )

        assert result.exit_code == 1
        assert "--objective is required" in result.output

    def test_missing_author(self, tmp_path, monkeypatch):
        """Should error when --author is missing."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        input_file = tmp_path / "input.md"
        input_file.write_text("Body content.")

        result = runner.invoke(
            main,
            ["from-file", str(input_file), "--name", "test", "--title", "Test", "--objective", "Test objective"],
        )

        assert result.exit_code == 1
        assert "--author is required" in result.output

    def test_sign_without_signed_by(self, tmp_path, monkeypatch):
        """Should error when --sign used without --signed-by."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Generate key first
        runner.invoke(main, ["generate-keys"])

        input_file = tmp_path / "input.md"
        input_file.write_text("Body content.")

        result = runner.invoke(
            main,
            [
                "from-file",
                str(input_file),
                "--name",
                "test",
                "--title",
                "Test",
                "--objective",
                "Test objective",
                "--author",
                "test@example.com",
                "--sign",
            ],
        )

        assert result.exit_code == 1
        assert "--signed-by is required" in result.output

    def test_sign_missing_key(self, tmp_path, monkeypatch):
        """Should error when signing key doesn't exist."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Don't generate key
        input_file = tmp_path / "input.md"
        input_file.write_text("Body content.")

        result = runner.invoke(
            main,
            [
                "from-file",
                str(input_file),
                "--name",
                "test",
                "--title",
                "Test",
                "--objective",
                "Test objective",
                "--author",
                "test@example.com",
                "--sign",
                "--signed-by",
                "test@example.com",
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_creates_dossier_from_markdown(self, tmp_path, monkeypatch):
        """Should create dossier from markdown file."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Create input file
        input_file = tmp_path / "input.md"
        input_file.write_text("# Hello World\n\nThis is the body.")

        result = runner.invoke(
            main,
            [
                "from-file",
                str(input_file),
                "--name",
                "test-dossier",
                "--title",
                "Test Dossier",
                "--objective",
                "Test objective",
                "--author",
                "test@example.com",
            ],
        )

        assert result.exit_code == 0
        output_file = tmp_path / "input.ds.md"
        assert output_file.exists()
        content = output_file.read_text()
        assert "name: test-dossier" in content
        assert "title: Test Dossier" in content
        assert "checksum:" in content

    def test_creates_dossier_with_meta_file(self, tmp_path, monkeypatch):
        """Should read metadata from JSON file."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Create input file
        input_file = tmp_path / "input.md"
        input_file.write_text("Body content here.")

        # Create meta file
        meta_file = tmp_path / "meta.json"
        meta_file.write_text(
            json.dumps(
                {
                    "name": "from-meta",
                    "title": "From Meta",
                    "objective": "Meta objective",
                    "authors": [{"name": "meta@example.com"}],
                }
            )
        )

        result = runner.invoke(main, ["from-file", str(input_file), "--meta", str(meta_file)])

        assert result.exit_code == 0
        content = (tmp_path / "input.ds.md").read_text()
        assert "name: from-meta" in content
        assert "title: From Meta" in content

    def test_creates_and_signs(self, tmp_path, monkeypatch):
        """Should create and sign dossier with --sign."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Generate key first
        runner.invoke(main, ["generate-keys"])

        # Create input file
        input_file = tmp_path / "input.md"
        input_file.write_text("Signed content.")

        result = runner.invoke(
            main,
            [
                "from-file",
                str(input_file),
                "--name",
                "signed-dossier",
                "--title",
                "Signed Dossier",
                "--objective",
                "Test objective",
                "--author",
                "test@example.com",
                "--sign",
                "--signed-by",
                "signer@example.com",
            ],
        )

        assert result.exit_code == 0
        content = (tmp_path / "input.ds.md").read_text()
        assert "signature:" in content


class TestValidate:
    """Tests for validate command."""

    def test_valid_file(self):
        """Should return 0 for valid file."""
        runner = CliRunner()
        result = runner.invoke(main, ["validate", str(FIXTURES_DIR / "valid" / "minimal.ds.md")])

        assert result.exit_code == 0
        assert "Valid" in result.output

    def test_invalid_file(self):
        """Should return 1 for invalid file."""
        runner = CliRunner()
        result = runner.invoke(main, ["validate", str(FIXTURES_DIR / "invalid" / "missing-title.ds.md")])

        assert result.exit_code == 1
        assert "Invalid" in result.output

    def test_json_output(self):
        """Should output JSON with --json."""
        runner = CliRunner()
        result = runner.invoke(main, ["validate", str(FIXTURES_DIR / "valid" / "minimal.ds.md"), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["valid"] is True


class TestChecksum:
    """Tests for checksum command."""

    def test_parse_error(self, tmp_path):
        """Should show error for unparseable file."""
        runner = CliRunner()

        dst = tmp_path / "bad.ds.md"
        dst.write_text("no frontmatter")

        result = runner.invoke(main, ["checksum", str(dst)])

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_parse_error_json(self, tmp_path):
        """Should show error in JSON format."""
        runner = CliRunner()

        dst = tmp_path / "bad.ds.md"
        dst.write_text("no frontmatter")

        result = runner.invoke(main, ["checksum", str(dst), "--json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

    def test_missing_checksum(self):
        """Should show missing status."""
        runner = CliRunner()
        result = runner.invoke(main, ["checksum", str(FIXTURES_DIR / "invalid" / "missing-checksum.ds.md")])

        assert result.exit_code == 1
        assert "missing" in result.output.lower()

    def test_update_json_output(self, tmp_path):
        """Should output JSON on update."""
        runner = CliRunner()

        src = FIXTURES_DIR / "valid" / "minimal.ds.md"
        dst = tmp_path / "test.ds.md"
        dst.write_text(src.read_text())

        result = runner.invoke(main, ["checksum", str(dst), "--update", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["updated"] is True
        assert "hash" in data

    def test_verify_valid_checksum(self):
        """Should return 0 for valid checksum."""
        runner = CliRunner()
        result = runner.invoke(main, ["checksum", str(FIXTURES_DIR / "valid" / "minimal.ds.md")])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_update_checksum(self, tmp_path):
        """Should update checksum in file."""
        runner = CliRunner()

        # Copy file to temp
        src = FIXTURES_DIR / "valid" / "minimal.ds.md"
        dst = tmp_path / "test.ds.md"
        dst.write_text(src.read_text())

        # Modify body to invalidate checksum
        content = dst.read_text()
        content = content.replace("This is the body content.", "This is modified body content.")
        dst.write_text(content)

        # Verify it's invalid first
        result = runner.invoke(main, ["checksum", str(dst)])
        assert result.exit_code == 1

        # Update checksum
        result = runner.invoke(main, ["checksum", str(dst), "--update"])
        assert result.exit_code == 0
        assert "Updated" in result.output

        # Verify it's now valid
        result = runner.invoke(main, ["checksum", str(dst)])
        assert result.exit_code == 0

    def test_json_output(self):
        """Should output JSON with --json."""
        runner = CliRunner()
        result = runner.invoke(main, ["checksum", str(FIXTURES_DIR / "valid" / "minimal.ds.md"), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "valid"


class TestSign:
    """Tests for sign command."""

    def test_sign_missing_key(self, tmp_path, monkeypatch):
        """Should error when key doesn't exist."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Don't generate key - just init
        (tmp_path / ".dossier").mkdir()

        src = FIXTURES_DIR / "valid" / "minimal.ds.md"
        dst = tmp_path / "test.ds.md"
        dst.write_text(src.read_text())

        result = runner.invoke(main, ["sign", str(dst), "--signed-by", "test@example.com"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_sign_with_default_key(self, tmp_path, monkeypatch):
        """Should sign file with default key."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Generate key
        runner.invoke(main, ["generate-keys"])

        # Copy file to temp
        src = FIXTURES_DIR / "valid" / "minimal.ds.md"
        dst = tmp_path / "test.ds.md"
        dst.write_text(src.read_text())

        result = runner.invoke(main, ["sign", str(dst), "--signed-by", "test@example.com"])

        assert result.exit_code == 0
        content = dst.read_text()
        assert "signature:" in content

    def test_sign_with_key_file(self, tmp_path, monkeypatch):
        """Should sign file with specific key file."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Generate key
        runner.invoke(main, ["generate-keys"])

        # Copy file to temp
        src = FIXTURES_DIR / "valid" / "minimal.ds.md"
        dst = tmp_path / "test.ds.md"
        dst.write_text(src.read_text())

        key_file = tmp_path / ".dossier" / "default.pem"

        result = runner.invoke(main, ["sign", str(dst), "--key-file", str(key_file), "--signed-by", "test@example.com"])

        assert result.exit_code == 0

    def test_sign_to_output_file(self, tmp_path, monkeypatch):
        """Should write to output file without modifying original."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Generate key
        runner.invoke(main, ["generate-keys"])

        # Copy file to temp
        src = FIXTURES_DIR / "valid" / "minimal.ds.md"
        original = tmp_path / "original.ds.md"
        original.write_text(src.read_text())
        original_content = original.read_text()

        output = tmp_path / "signed.ds.md"

        result = runner.invoke(main, ["sign", str(original), "--signed-by", "test@example.com", "-o", str(output)])

        assert result.exit_code == 0
        assert output.exists()
        assert "signature:" in output.read_text()
        # Original unchanged
        assert original.read_text() == original_content


class TestVerify:
    """Tests for verify command."""

    def test_verify_invalid_schema(self):
        """Should show schema errors."""
        runner = CliRunner()
        result = runner.invoke(main, ["verify", str(FIXTURES_DIR / "invalid" / "missing-title.ds.md")])

        assert result.exit_code == 1
        assert "Schema:" in result.output
        assert "invalid" in result.output.lower()

    def test_verify_invalid_checksum(self, tmp_path):
        """Should show checksum error."""
        runner = CliRunner()

        # Create file with wrong checksum
        dst = tmp_path / "test.ds.md"
        dst.write_text("""---
schema_version: "1.0.0"
title: Test Dossier
version: "1.0.0"
status: stable
objective: This is the objective
authors:
  - name: Test
checksum:
  algorithm: sha256
  hash: 0000000000000000000000000000000000000000000000000000000000000000
---

# Test

Body content.
""")

        result = runner.invoke(main, ["verify", str(dst)])

        assert result.exit_code == 1
        assert "Checksum:" in result.output
        assert "invalid" in result.output.lower()

    def test_verify_parse_error(self, tmp_path):
        """Should show parse error."""
        runner = CliRunner()

        dst = tmp_path / "bad.ds.md"
        dst.write_text("no frontmatter here")

        result = runner.invoke(main, ["verify", str(dst)])

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_verify_parse_error_json(self, tmp_path):
        """Should show parse error in JSON."""
        runner = CliRunner()

        dst = tmp_path / "bad.ds.md"
        dst.write_text("no frontmatter here")

        result = runner.invoke(main, ["verify", str(dst), "--json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

    def test_verify_valid_unsigned(self):
        """Should verify valid unsigned dossier."""
        runner = CliRunner()
        result = runner.invoke(main, ["verify", str(FIXTURES_DIR / "valid" / "minimal.ds.md")])

        assert result.exit_code == 0
        assert "Schema:    valid" in result.output
        assert "Checksum:  valid" in result.output
        assert "unsigned" in result.output.lower()

    def test_verify_signed_dossier(self, tmp_path, monkeypatch):
        """Should verify signed dossier."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Generate key and sign
        runner.invoke(main, ["generate-keys"])
        src = FIXTURES_DIR / "valid" / "minimal.ds.md"
        dst = tmp_path / "test.ds.md"
        dst.write_text(src.read_text())
        runner.invoke(main, ["sign", str(dst), "--signed-by", "test@example.com"])

        result = runner.invoke(main, ["verify", str(dst)])

        assert result.exit_code == 0
        assert "Signature: valid" in result.output

    def test_json_output(self):
        """Should output JSON with --json."""
        runner = CliRunner()
        result = runner.invoke(main, ["verify", str(FIXTURES_DIR / "valid" / "minimal.ds.md"), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["valid"] is True
        assert data["schema"]["valid"] is True
        assert data["checksum"]["status"] == "valid"


class TestInfo:
    """Tests for info command."""

    def test_parse_error(self, tmp_path):
        """Should show error for unparseable file."""
        runner = CliRunner()

        dst = tmp_path / "bad.ds.md"
        dst.write_text("no frontmatter")

        result = runner.invoke(main, ["info", str(dst)])

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_parse_error_json(self, tmp_path):
        """Should show error in JSON format."""
        runner = CliRunner()

        dst = tmp_path / "bad.ds.md"
        dst.write_text("no frontmatter")

        result = runner.invoke(main, ["info", str(dst), "--json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

    def test_displays_metadata(self):
        """Should display frontmatter fields."""
        runner = CliRunner()
        result = runner.invoke(main, ["info", str(FIXTURES_DIR / "valid" / "minimal.ds.md")])

        assert result.exit_code == 0
        assert "Title:" in result.output
        assert "Version:" in result.output
        assert "Status:" in result.output

    def test_json_output(self):
        """Should output JSON with --json."""
        runner = CliRunner()
        result = runner.invoke(main, ["info", str(FIXTURES_DIR / "valid" / "minimal.ds.md"), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "title" in data
        assert "version" in data


class TestKeys:
    """Tests for keys.py helper functions."""

    def test_get_dossier_dir(self, tmp_path, monkeypatch):
        """Should return ~/.dossier path."""
        monkeypatch.setenv("HOME", str(tmp_path))
        assert get_dossier_dir() == tmp_path / ".dossier"

    def test_get_private_key_path(self, tmp_path, monkeypatch):
        """Should return path to private key."""
        monkeypatch.setenv("HOME", str(tmp_path))
        assert get_private_key_path("test") == tmp_path / ".dossier" / "test.pem"

    def test_get_public_key_path(self, tmp_path, monkeypatch):
        """Should return path to public key."""
        monkeypatch.setenv("HOME", str(tmp_path))
        assert get_public_key_path("test") == tmp_path / ".dossier" / "test.pub"


# --- Registry CLI tests ---


class TestList:
    """Tests for list command."""

    @respx.mock
    def test_list_empty(self, monkeypatch):
        """Should show message when no dossiers found."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                200,
                json={"dossiers": [], "pagination": {"page": 1, "per_page": 20, "total": 0}},
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "No dossiers found" in result.output

    @respx.mock
    def test_list_registry_error(self, monkeypatch):
        """Should show error on registry failure."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(500, json={"error": {"code": "INTERNAL_ERROR", "message": "Server error"}})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["list"])

        assert result.exit_code == 1
        assert "Error" in result.output

    @respx.mock
    def test_list_dossiers(self, monkeypatch):
        """Should list dossiers from registry."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                200,
                json={
                    "dossiers": [
                        {"name": "myorg/deploy", "version": "1.0.0", "title": "Deploy"},
                        {"name": "myorg/backup", "version": "2.0.0", "title": "Backup"},
                    ],
                    "pagination": {"page": 1, "per_page": 20, "total": 2},
                },
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "myorg/deploy" in result.output
        assert "myorg/backup" in result.output

    @respx.mock
    def test_list_json_output(self, monkeypatch):
        """Should output JSON with --json."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                200,
                json={"dossiers": [], "pagination": {"page": 1, "per_page": 20, "total": 0}},
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["list", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "dossiers" in data


class TestGet:
    """Tests for get command."""

    @respx.mock
    def test_get_dossier(self, monkeypatch):
        """Should display dossier metadata."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers/myorg/deploy").mock(
            return_value=Response(
                200,
                json={
                    "name": "myorg/deploy",
                    "title": "Deploy to Production",
                    "version": "1.2.0",
                    "status": "stable",
                },
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["get", "myorg/deploy"])

        assert result.exit_code == 0
        assert "myorg/deploy" in result.output
        assert "Deploy to Production" in result.output
        assert "1.2.0" in result.output

    @respx.mock
    def test_get_with_version(self, monkeypatch):
        """Should request specific version."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        route = respx.get("https://registry.test/api/v1/dossiers/myorg/deploy").mock(
            return_value=Response(200, json={"name": "myorg/deploy", "version": "1.0.0"})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["get", "myorg/deploy@1.0.0"])

        assert result.exit_code == 0
        assert route.calls[0].request.url.params["version"] == "1.0.0"

    @respx.mock
    def test_get_json_output(self, monkeypatch):
        """Should output JSON with --json."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers/myorg/deploy").mock(
            return_value=Response(200, json={"name": "myorg/deploy", "version": "1.0.0"})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["get", "myorg/deploy", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "myorg/deploy"

    @respx.mock
    def test_get_not_found(self, monkeypatch):
        """Should error on 404."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers/myorg/missing").mock(
            return_value=Response(404, json={"error": {"code": "DOSSIER_NOT_FOUND", "message": "Dossier not found"}})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["get", "myorg/missing"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestPull:
    """Tests for pull command (caching to ~/.dossier/cache/)."""

    @respx.mock
    def test_pull_dossier(self, tmp_path, monkeypatch):
        """Should cache dossier to ~/.dossier/cache/."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        content = """---
title: Deploy
version: "1.0.0"
---

# Deploy
"""
        # Mock metadata endpoint (to resolve version)
        respx.get("https://registry.test/api/v1/dossiers/myorg/deploy").mock(
            return_value=Response(200, json={"name": "myorg/deploy", "version": "1.0.0", "title": "Deploy"})
        )
        # Mock content endpoint
        respx.get("https://registry.test/api/v1/dossiers/myorg/deploy/content").mock(
            return_value=Response(200, text=content, headers={"X-Dossier-Digest": "sha256:abc123"})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["pull", "myorg/deploy"])

        assert result.exit_code == 0
        assert "Cached" in result.output

        # Check file was cached
        cache_file = tmp_path / ".dossier" / "cache" / "myorg" / "deploy" / "1.0.0.ds.md"
        assert cache_file.exists()
        assert cache_file.read_text() == content

        # Check metadata file was created
        meta_file = tmp_path / ".dossier" / "cache" / "myorg" / "deploy" / "1.0.0.meta.json"
        assert meta_file.exists()

    @respx.mock
    def test_pull_with_version(self, tmp_path, monkeypatch):
        """Should request specific version."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        content = "---\nversion: '1.0.0'\n---\ncontent"
        route = respx.get("https://registry.test/api/v1/dossiers/myorg/deploy/content").mock(
            return_value=Response(200, text=content, headers={})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["pull", "myorg/deploy@1.0.0"])

        assert result.exit_code == 0
        assert route.calls[0].request.url.params["version"] == "1.0.0"

        # Check cache
        cache_file = tmp_path / ".dossier" / "cache" / "myorg" / "deploy" / "1.0.0.ds.md"
        assert cache_file.exists()

    @respx.mock
    def test_pull_skips_if_cached(self, tmp_path, monkeypatch):
        """Should skip download if already cached."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Pre-create cache
        cache_dir = tmp_path / ".dossier" / "cache" / "myorg" / "deploy"
        cache_dir.mkdir(parents=True)
        (cache_dir / "1.0.0.ds.md").write_text("cached content")
        (cache_dir / "1.0.0.meta.json").write_text(TEST_CACHE_META)

        runner = CliRunner()
        result = runner.invoke(main, ["pull", "myorg/deploy@1.0.0"])

        assert result.exit_code == 0
        assert "already cached" in result.output

    @respx.mock
    def test_pull_force_redownloads(self, tmp_path, monkeypatch):
        """Should re-download with --force even if cached."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Pre-create cache
        cache_dir = tmp_path / ".dossier" / "cache" / "myorg" / "deploy"
        cache_dir.mkdir(parents=True)
        (cache_dir / "1.0.0.ds.md").write_text("old content")
        (cache_dir / "1.0.0.meta.json").write_text(TEST_CACHE_META)

        respx.get("https://registry.test/api/v1/dossiers/myorg/deploy/content").mock(
            return_value=Response(200, text="new content", headers={})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["pull", "myorg/deploy@1.0.0", "--force"])

        assert result.exit_code == 0
        assert "Cached" in result.output

        # Check content was updated
        cache_file = cache_dir / "1.0.0.ds.md"
        assert cache_file.read_text() == "new content"

    @respx.mock
    def test_pull_not_found(self, monkeypatch):
        """Should error on 404."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers/myorg/missing").mock(
            return_value=Response(404, json={"error": {"code": "DOSSIER_NOT_FOUND", "message": "Dossier not found"}})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["pull", "myorg/missing"])

        assert result.exit_code == 1


class TestExport:
    """Tests for export command."""

    @respx.mock
    def test_export_default_filename(self, tmp_path, monkeypatch):
        """Should export to default filename."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")
        monkeypatch.chdir(tmp_path)

        content = "---\ntitle: Deploy\n---\n# Deploy"
        respx.get("https://registry.test/api/v1/dossiers/myorg/deploy/content").mock(
            return_value=Response(200, text=content, headers={"X-Dossier-Digest": "sha256:abc123"})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["export", "myorg/deploy"])

        assert result.exit_code == 0
        assert "Exported" in result.output

        output_file = tmp_path / "myorg-deploy.ds.md"
        assert output_file.exists()
        assert output_file.read_text() == content

    @respx.mock
    def test_export_with_output(self, tmp_path, monkeypatch):
        """Should save to specified output file."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        respx.get("https://registry.test/api/v1/dossiers/myorg/deploy/content").mock(
            return_value=Response(200, text="content", headers={})
        )

        output_file = tmp_path / "custom.ds.md"

        runner = CliRunner()
        result = runner.invoke(main, ["export", "myorg/deploy", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.read_text() == "content"

    @respx.mock
    def test_export_stdout(self, monkeypatch):
        """Should print to stdout with --stdout."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        content = "---\ntitle: Deploy\n---\n# Deploy"
        respx.get("https://registry.test/api/v1/dossiers/myorg/deploy/content").mock(
            return_value=Response(200, text=content, headers={})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["export", "myorg/deploy", "--stdout"])

        assert result.exit_code == 0
        assert content in result.output


class TestInstallSkill:
    """Tests for install-skill command."""

    @respx.mock
    def test_install_skill_success(self, tmp_path, monkeypatch):
        """Should install skill to ~/.claude/skills/<name>/SKILL.md."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        content = "---\ntitle: Start Issue\n---\n# Start Issue Workflow"
        # Mock version resolution
        respx.get("https://registry.test/api/v1/dossiers/imboard-ai/skills/start-issue").mock(
            return_value=Response(200, json={"version": "1.0.0"})
        )
        respx.get("https://registry.test/api/v1/dossiers/imboard-ai/skills/start-issue/content").mock(
            return_value=Response(200, text=content, headers={})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["install-skill", "imboard-ai/skills/start-issue"])

        assert result.exit_code == 0
        assert "Installed skill 'start-issue'" in result.output
        assert "(v1.0.0)" in result.output

        skill_file = tmp_path / ".claude" / "skills" / "start-issue" / "SKILL.md"
        assert skill_file.exists()
        assert skill_file.read_text() == content

    @respx.mock
    def test_install_skill_already_exists(self, tmp_path, monkeypatch):
        """Should fail if skill already exists without --force."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        # Create existing skill
        skill_dir = tmp_path / ".claude" / "skills" / "start-issue"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("existing content")

        runner = CliRunner()
        result = runner.invoke(main, ["install-skill", "imboard-ai/skills/start-issue"])

        assert result.exit_code == 1
        assert "already exists" in result.output
        assert "--force" in result.output

    @respx.mock
    def test_install_skill_force_overwrite(self, tmp_path, monkeypatch):
        """Should overwrite existing skill with --force."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        # Create existing skill
        skill_dir = tmp_path / ".claude" / "skills" / "start-issue"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("old content")

        new_content = "---\ntitle: Updated\n---\n# Updated content"
        respx.get("https://registry.test/api/v1/dossiers/myorg/skills/start-issue").mock(
            return_value=Response(200, json={"version": "2.0.0"})
        )
        respx.get("https://registry.test/api/v1/dossiers/myorg/skills/start-issue/content").mock(
            return_value=Response(200, text=new_content, headers={})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["install-skill", "myorg/skills/start-issue", "--force"])

        assert result.exit_code == 0
        assert "Installed skill 'start-issue'" in result.output

        skill_file = skill_dir / "SKILL.md"
        assert skill_file.read_text() == new_content

    @respx.mock
    def test_install_skill_with_version(self, tmp_path, monkeypatch):
        """Should install specific version when specified."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        content = "---\ntitle: Skill v1.2.0\n---\n# Content"
        # No version resolution needed when version is specified
        respx.get("https://registry.test/api/v1/dossiers/myorg/my-skill/content").mock(
            return_value=Response(200, text=content, headers={})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["install-skill", "myorg/my-skill@1.2.0"])

        assert result.exit_code == 0
        assert "Installed skill 'my-skill'" in result.output

        skill_file = tmp_path / ".claude" / "skills" / "my-skill" / "SKILL.md"
        assert skill_file.exists()

    @respx.mock
    def test_install_skill_registry_error(self, tmp_path, monkeypatch):
        """Should handle registry errors gracefully."""
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        respx.get("https://registry.test/api/v1/dossiers/myorg/nonexistent").mock(
            return_value=Response(404, json={"error": {"message": "Dossier not found"}})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["install-skill", "myorg/nonexistent"])

        assert result.exit_code == 1
        assert "Error" in result.output


class TestCacheCommands:
    """Tests for cache subcommands."""

    def test_cache_list_empty(self, tmp_path, monkeypatch):
        """Should show empty message when no cached dossiers."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["cache", "list"])

        assert result.exit_code == 0
        assert "No cached dossiers" in result.output

    def test_cache_list_shows_cached(self, tmp_path, monkeypatch):
        """Should list cached dossiers."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create cache entry
        cache_dir = tmp_path / ".dossier" / "cache" / "myorg" / "deploy"
        cache_dir.mkdir(parents=True)
        (cache_dir / "1.0.0.ds.md").write_text("content")
        (cache_dir / "1.0.0.meta.json").write_text(TEST_CACHE_META)

        runner = CliRunner()
        result = runner.invoke(main, ["cache", "list"])

        assert result.exit_code == 0
        assert "myorg/deploy" in result.output
        assert "1.0.0" in result.output

    def test_cache_list_json(self, tmp_path, monkeypatch):
        """Should output JSON when requested."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create cache entry
        cache_dir = tmp_path / ".dossier" / "cache" / "myorg" / "deploy"
        cache_dir.mkdir(parents=True)
        (cache_dir / "1.0.0.ds.md").write_text("content")
        (cache_dir / "1.0.0.meta.json").write_text(TEST_CACHE_META)

        runner = CliRunner()
        result = runner.invoke(main, ["cache", "list", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["name"] == "myorg/deploy"

    def test_cache_clean_specific(self, tmp_path, monkeypatch):
        """Should clean specific dossier."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create cache entry
        cache_dir = tmp_path / ".dossier" / "cache" / "myorg" / "deploy"
        cache_dir.mkdir(parents=True)
        cache_file = cache_dir / "1.0.0.ds.md"
        meta_file = cache_dir / "1.0.0.meta.json"
        cache_file.write_text("content")
        meta_file.write_text(TEST_CACHE_META)

        runner = CliRunner()
        result = runner.invoke(main, ["cache", "clean", "myorg/deploy"])

        assert result.exit_code == 0
        assert "Removed" in result.output
        assert not cache_file.exists()

    def test_cache_clean_all(self, tmp_path, monkeypatch):
        """Should clean all cached dossiers."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create cache entries
        for name in ["deploy", "backup"]:
            cache_dir = tmp_path / ".dossier" / "cache" / "myorg" / name
            cache_dir.mkdir(parents=True)
            (cache_dir / "1.0.0.ds.md").write_text("content")
            (cache_dir / "1.0.0.meta.json").write_text(TEST_CACHE_META)

        runner = CliRunner()
        result = runner.invoke(main, ["cache", "clean", "--all", "-y"])

        assert result.exit_code == 0
        assert "Removed 2" in result.output

        # Verify cache is empty
        cache_dir = tmp_path / ".dossier" / "cache"
        assert not cache_dir.exists()


class TestLogout:
    """Tests for logout command."""

    def test_logout_removes_credentials(self, tmp_path, monkeypatch):
        """Should remove credentials file."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text('{"token": "my-token", "username": "alice", "orgs": []}')

        runner = CliRunner()
        result = runner.invoke(main, ["logout"])

        assert result.exit_code == 0
        assert "Logged out" in result.output
        assert not (dossier_dir / "credentials").exists()

    def test_logout_not_logged_in(self, tmp_path, monkeypatch):
        """Should show message when not logged in."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["logout"])

        assert result.exit_code == 0
        assert "Not logged in" in result.output


class TestWhoami:
    """Tests for whoami command."""

    def test_whoami_not_logged_in(self, tmp_path, monkeypatch):
        """Should error when not logged in."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["whoami"])

        assert result.exit_code == 1
        assert "Not logged in" in result.output

    def test_whoami_shows_user(self, tmp_path, monkeypatch):
        """Should display user info from local credentials."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text('{"token": "my-token", "username": "alice", "orgs": ["org1", "org2"]}')

        runner = CliRunner()
        result = runner.invoke(main, ["whoami"])

        assert result.exit_code == 0
        assert "alice" in result.output
        assert "org1" in result.output

    def test_whoami_expired_credentials(self, tmp_path, monkeypatch):
        """Should show expired message for expired credentials."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create expired credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text(
            '{"token": "my-token", "username": "alice", "orgs": [], "expires_at": "2020-01-01T00:00:00+00:00"}'
        )

        runner = CliRunner()
        result = runner.invoke(main, ["whoami"])

        assert result.exit_code == 1
        assert "expired" in result.output.lower()


class TestPublish:
    """Tests for publish command."""

    def test_publish_not_logged_in(self, tmp_path, monkeypatch):
        """Should error when not logged in."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            main, ["publish", str(FIXTURES_DIR / "valid" / "minimal.ds.md"), "--namespace", "myorg/tools"]
        )

        assert result.exit_code == 1
        assert "Not logged in" in result.output

    @respx.mock
    def test_publish_dossier(self, tmp_path, monkeypatch):
        """Should publish valid dossier."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        # Create credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text('{"token": "my-token", "username": "alice", "orgs": []}')

        # Create dossier with name
        dossier_file = tmp_path / "deploy.ds.md"
        dossier_file.write_text("""---
schema_version: "1.0.0"
title: Deploy
version: "1.0.0"
status: draft
objective: Deploy the app
name: deploy
authors:
  - name: Alice
checksum:
  algorithm: sha256
  hash: 6bb135eeeff94e0e72479e59796ec87ede1be5f425946c882691498957c21568
---

# Deploy
""")

        respx.post("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                201,
                json={"name": "myorg/deploy", "version": "1.0.0", "url": "https://registry.test/myorg/deploy"},
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["publish", str(dossier_file), "--namespace", "myorg/tools"])

        assert result.exit_code == 0
        assert "Published" in result.output
        assert "myorg/deploy" in result.output

    @respx.mock
    def test_publish_with_changelog(self, tmp_path, monkeypatch):
        """Should include changelog in request."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        # Create credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text('{"token": "my-token", "username": "alice", "orgs": []}')

        # Create dossier with name
        dossier_file = tmp_path / "deploy.ds.md"
        dossier_file.write_text("""---
schema_version: "1.0.0"
title: Deploy
version: "1.0.0"
status: draft
objective: Deploy the app
name: deploy
authors:
  - name: Alice
checksum:
  algorithm: sha256
  hash: 6bb135eeeff94e0e72479e59796ec87ede1be5f425946c882691498957c21568
---

# Deploy
""")

        route = respx.post("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(201, json={"name": "myorg/deploy", "version": "1.0.0"})
        )

        runner = CliRunner()
        result = runner.invoke(
            main, ["publish", str(dossier_file), "--namespace", "myorg/tools", "--changelog", "Fixed bug"]
        )

        assert result.exit_code == 0
        body = json.loads(route.calls[0].request.content)
        assert body["changelog"] == "Fixed bug"

    @respx.mock
    def test_publish_version_conflict(self, tmp_path, monkeypatch):
        """Should show conflict error on 409."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        # Create credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text('{"token": "my-token", "username": "alice", "orgs": []}')

        # Create dossier with name
        dossier_file = tmp_path / "deploy.ds.md"
        dossier_file.write_text("""---
schema_version: "1.0.0"
title: Deploy
version: "1.0.0"
status: draft
objective: Deploy the app
name: deploy
authors:
  - name: Alice
checksum:
  algorithm: sha256
  hash: 6bb135eeeff94e0e72479e59796ec87ede1be5f425946c882691498957c21568
---

# Deploy
""")

        respx.post("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(
                409, json={"error": {"code": "VERSION_EXISTS", "message": "Version 1.0.0 already exists"}}
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["publish", str(dossier_file), "--namespace", "myorg/tools"])

        assert result.exit_code == 1
        assert "conflict" in result.output.lower()

    def test_publish_invalid_schema(self, tmp_path, monkeypatch):
        """Should error on schema validation failure."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text('{"token": "my-token", "username": "alice", "orgs": []}')

        # Create invalid dossier (missing required fields)
        dossier_file = tmp_path / "invalid.ds.md"
        dossier_file.write_text("""---
schema_version: "1.0.0"
name: invalid
---

# Invalid
""")

        runner = CliRunner()
        result = runner.invoke(main, ["publish", str(dossier_file), "--namespace", "myorg/tools"])

        assert result.exit_code == 1
        assert "Validation errors" in result.output

    def test_publish_invalid_checksum(self, tmp_path, monkeypatch):
        """Should error on checksum validation failure."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)

        # Create credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text('{"token": "my-token", "username": "alice", "orgs": []}')

        # Create dossier with wrong checksum (valid format but wrong value)
        dossier_file = tmp_path / "bad-checksum.ds.md"
        dossier_file.write_text("""---
schema_version: "1.0.0"
title: Bad Checksum
version: "1.0.0"
status: draft
objective: Test invalid checksum
name: bad
authors:
  - name: Alice
checksum:
  algorithm: sha256
  hash: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
---

# Bad Checksum
""")

        runner = CliRunner()
        result = runner.invoke(main, ["publish", str(dossier_file), "--namespace", "myorg/tools"])

        assert result.exit_code == 1
        assert "Checksum error" in result.output

    @respx.mock
    def test_publish_unauthorized(self, tmp_path, monkeypatch):
        """Should show session expired on 401."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        # Create credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text('{"token": "my-token", "username": "alice", "orgs": []}')

        # Create valid dossier
        dossier_file = tmp_path / "deploy.ds.md"
        dossier_file.write_text("""---
schema_version: "1.0.0"
title: Deploy
version: "1.0.0"
status: draft
objective: Deploy the app
name: deploy
authors:
  - name: Alice
checksum:
  algorithm: sha256
  hash: 6bb135eeeff94e0e72479e59796ec87ede1be5f425946c882691498957c21568
---

# Deploy
""")

        respx.post("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(401, json={"error": {"code": "UNAUTHORIZED", "message": "Invalid token"}})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["publish", str(dossier_file), "--namespace", "myorg/tools"])

        assert result.exit_code == 1
        assert "expired" in result.output.lower()

    @respx.mock
    def test_publish_forbidden(self, tmp_path, monkeypatch):
        """Should show permission denied on 403."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        # Create credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text('{"token": "my-token", "username": "alice", "orgs": []}')

        # Create valid dossier
        dossier_file = tmp_path / "deploy.ds.md"
        dossier_file.write_text("""---
schema_version: "1.0.0"
title: Deploy
version: "1.0.0"
status: draft
objective: Deploy the app
name: forbidden-deploy
authors:
  - name: Alice
checksum:
  algorithm: sha256
  hash: 6bb135eeeff94e0e72479e59796ec87ede1be5f425946c882691498957c21568
---

# Deploy
""")

        respx.post("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(403, json={"error": {"code": "FORBIDDEN", "message": "Not authorized"}})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["publish", str(dossier_file), "--namespace", "myorg/tools"])

        assert result.exit_code == 1
        assert "Permission denied" in result.output


class TestCreateSignChecksum:
    """Tests for create --sign checksum fix (Issue 1)."""

    def test_create_with_sign_produces_valid_checksum(self, tmp_path, monkeypatch):
        """Checksum should be valid immediately after create --sign.

        This tests the fix for Issue 1: When creating a dossier with --sign,
        the checksum must be calculated AFTER frontmatter normalization to
        ensure it matches what will be verified later.
        """
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        # Generate key first
        runner.invoke(main, ["generate-keys"])

        # Create input file WITH trailing newline (this is the common case that
        # triggers the bug - frontmatter strips trailing newlines)
        input_file = tmp_path / "test.md"
        input_file.write_text("# Test content\n\nThis is body content.\n")

        output_file = tmp_path / "test.ds.md"

        # Create and sign dossier
        result = runner.invoke(
            main,
            [
                "from-file",
                str(input_file),
                "--name",
                "test",
                "--title",
                "Test",
                "--objective",
                "Test objective",
                "--author",
                "Test Author",
                "--sign",
                "--signed-by",
                "Test Author",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify should pass immediately - this was failing before the fix
        verify_result = runner.invoke(main, ["verify", str(output_file)])

        assert verify_result.exit_code == 0
        assert "Checksum:  valid" in verify_result.output
        assert "Signature: valid" in verify_result.output

    def test_create_with_sign_checksum_valid_json(self, tmp_path, monkeypatch):
        """Same as above but verify using JSON output."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        runner.invoke(main, ["generate-keys"])

        input_file = tmp_path / "test.md"
        input_file.write_text("Body with trailing newline\n")
        output_file = tmp_path / "test.ds.md"

        runner.invoke(
            main,
            [
                "from-file",
                str(input_file),
                "--name",
                "test",
                "--title",
                "Test",
                "--objective",
                "Testing the checksum validation",
                "--author",
                "Author",
                "--sign",
                "--signed-by",
                "Author",
                "-o",
                str(output_file),
            ],
        )

        verify_result = runner.invoke(main, ["verify", str(output_file), "--json"])

        assert verify_result.exit_code == 0
        data = json.loads(verify_result.output)
        assert data["valid"] is True
        assert data["checksum"]["status"] == "valid"
        assert data["signature"]["status"] == "valid"


class TestPublishPropagationNote:
    """Tests for publish propagation note (Issue 2)."""

    @respx.mock
    def test_publish_shows_propagation_note(self, tmp_path, monkeypatch):
        """Publish should show a note about CDN propagation delay."""
        monkeypatch.setattr("dossier_tools.signing.keys.Path.home", lambda: tmp_path)
        monkeypatch.setenv("DOSSIER_REGISTRY_URL", "https://registry.test")

        # Create credentials
        dossier_dir = tmp_path / ".dossier"
        dossier_dir.mkdir()
        (dossier_dir / "credentials").write_text('{"token": "my-token", "username": "alice", "orgs": []}')

        # Create valid dossier
        dossier_file = tmp_path / "deploy.ds.md"
        dossier_file.write_text("""---
schema_version: "1.0.0"
title: Deploy
version: "1.0.0"
status: draft
objective: Deploy the app
name: deploy
authors:
  - name: Alice
checksum:
  algorithm: sha256
  hash: 6bb135eeeff94e0e72479e59796ec87ede1be5f425946c882691498957c21568
---

# Deploy
""")

        respx.post("https://registry.test/api/v1/dossiers").mock(
            return_value=Response(201, json={"name": "myorg/deploy", "version": "1.0.0"})
        )

        runner = CliRunner()
        result = runner.invoke(main, ["publish", str(dossier_file), "--namespace", "myorg/tools"])

        assert result.exit_code == 0
        assert "Published" in result.output
        # Check for the propagation note
        assert "may take" in result.output.lower()
        assert "dossier list" in result.output


class TestSignedByWarning:
    """Tests for signed_by mismatch warning (Issue 3)."""

    def test_create_sign_warns_when_signed_by_differs_from_author(self, tmp_path, monkeypatch):
        """Create --sign should warn when --signed-by doesn't match --author."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        runner.invoke(main, ["generate-keys"])

        input_file = tmp_path / "test.md"
        input_file.write_text("Body content")
        output_file = tmp_path / "test.ds.md"

        result = runner.invoke(
            main,
            [
                "from-file",
                str(input_file),
                "--name",
                "test",
                "--title",
                "Test",
                "--objective",
                "Testing",
                "--author",
                "Real Author",
                "--sign",
                "--signed-by",
                "Different Person",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "Different Person" in result.output
        assert "does not match any author" in result.output
        assert "self-reported" in result.output.lower()

    def test_create_sign_no_warning_when_signed_by_matches_author(self, tmp_path, monkeypatch):
        """Create --sign should NOT warn when --signed-by matches --author."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        runner.invoke(main, ["generate-keys"])

        input_file = tmp_path / "test.md"
        input_file.write_text("Body content")
        output_file = tmp_path / "test.ds.md"

        result = runner.invoke(
            main,
            [
                "from-file",
                str(input_file),
                "--name",
                "test",
                "--title",
                "Test",
                "--objective",
                "Testing",
                "--author",
                "Same Person",
                "--sign",
                "--signed-by",
                "Same Person",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "Warning" not in result.output

    def test_sign_warns_when_signed_by_differs_from_author(self, tmp_path, monkeypatch):
        """Sign command should warn when --signed-by doesn't match authors."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        runner.invoke(main, ["generate-keys"])

        # Create a dossier first (unsigned)
        dossier_file = tmp_path / "test.ds.md"
        dossier_file.write_text("""---
schema_version: "1.0.0"
title: Test
version: "1.0.0"
status: draft
objective: Testing
name: test
authors:
  - name: Alice
  - name: Bob
checksum:
  algorithm: sha256
  hash: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
---

test""")

        result = runner.invoke(
            main,
            ["sign", str(dossier_file), "--signed-by", "Charlie"],
        )

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "Charlie" in result.output
        assert "does not match any author" in result.output

    def test_sign_no_warning_when_signed_by_matches_author(self, tmp_path, monkeypatch):
        """Sign command should NOT warn when --signed-by matches an author."""
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()

        runner.invoke(main, ["generate-keys"])

        dossier_file = tmp_path / "test.ds.md"
        dossier_file.write_text("""---
schema_version: "1.0.0"
title: Test
version: "1.0.0"
status: draft
objective: Testing
name: test
authors:
  - name: Alice
  - name: Bob
checksum:
  algorithm: sha256
  hash: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
---

test""")

        result = runner.invoke(
            main,
            ["sign", str(dossier_file), "--signed-by", "Bob"],
        )

        assert result.exit_code == 0
        assert "Warning" not in result.output
