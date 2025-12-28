"""Tests for the signing module."""

from datetime import UTC, datetime

import pytest

from dossier_tools.signing import (
    SignatureInfo,
    SignatureStatus,
    SignatureVerificationResult,
    sign_dossier,
    verify_dossier_signature,
)
from dossier_tools.signing.ed25519 import Ed25519Signer, Ed25519Verifier
from dossier_tools.signing.registry import VerifierRegistry, default_registry


class TestEd25519Signer:
    """Tests for Ed25519Signer."""

    def test_generate_creates_valid_signer(self):
        """Should generate a new key pair."""
        signer = Ed25519Signer.generate()

        assert signer.algorithm == "ed25519"
        assert len(signer.get_public_key()) > 0

    def test_sign_returns_signature_info(self):
        """Should return SignatureInfo with all fields."""
        signer = Ed25519Signer.generate()

        sig_info = signer.sign("test content", "test@example.com", "key-123")

        assert isinstance(sig_info, SignatureInfo)
        assert sig_info.algorithm == "ed25519"
        assert sig_info.public_key == signer.get_public_key()
        assert len(sig_info.signature) > 0
        assert sig_info.signed_by == "test@example.com"
        assert sig_info.key_id == "key-123"
        assert isinstance(sig_info.timestamp, datetime)

    def test_sign_without_key_id(self):
        """Should work without key_id."""
        signer = Ed25519Signer.generate()

        sig_info = signer.sign("test content", "test@example.com")

        assert sig_info.key_id is None

    def test_from_pem_file(self, tmp_path):
        """Should load signer from PEM file."""
        # Generate a key and save it
        original_signer = Ed25519Signer.generate()
        pem_path = tmp_path / "test-key.pem"
        pem_path.write_text(original_signer.get_private_key_pem())

        # Load it back
        loaded_signer = Ed25519Signer.from_pem_file(pem_path)

        assert loaded_signer.get_public_key() == original_signer.get_public_key()

    def test_from_pem_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            Ed25519Signer.from_pem_file("/nonexistent/path.pem")

    def test_from_env_pem_format(self, monkeypatch):
        """Should load signer from env var with PEM format."""
        original_signer = Ed25519Signer.generate()
        pem_content = original_signer.get_private_key_pem()
        monkeypatch.setenv("TEST_SIGNING_KEY", pem_content)

        loaded_signer = Ed25519Signer.from_env("TEST_SIGNING_KEY")

        assert loaded_signer.get_public_key() == original_signer.get_public_key()

    def test_from_env_not_set(self):
        """Should raise ValueError when env var not set."""
        with pytest.raises(ValueError, match="not set"):
            Ed25519Signer.from_env("NONEXISTENT_VAR_12345")

    def test_get_private_key_pem(self):
        """Should return PEM-encoded private key."""
        signer = Ed25519Signer.generate()

        pem = signer.get_private_key_pem()

        assert pem.startswith("-----BEGIN PRIVATE KEY-----")
        assert pem.strip().endswith("-----END PRIVATE KEY-----")


class TestEd25519Verifier:
    """Tests for Ed25519Verifier."""

    def test_verify_valid_signature(self):
        """Should return VALID for correct signature."""
        signer = Ed25519Signer.generate()
        verifier = Ed25519Verifier()
        content = "test content to sign"

        sig_info = signer.sign(content, "test@example.com")
        result = verifier.verify(
            content,
            {
                "algorithm": sig_info.algorithm,
                "public_key": sig_info.public_key,
                "signature": sig_info.signature,
                "signed_by": sig_info.signed_by,
                "timestamp": sig_info.timestamp.isoformat(),
            },
        )

        assert result.status == SignatureStatus.VALID
        assert result.valid is True
        assert result.algorithm == "ed25519"
        assert result.signed_by == "test@example.com"
        assert result.error is None

    def test_verify_invalid_signature(self):
        """Should return INVALID for wrong signature."""
        signer = Ed25519Signer.generate()
        verifier = Ed25519Verifier()

        sig_info = signer.sign("original content", "test@example.com")
        result = verifier.verify(
            "tampered content",  # Different content
            {
                "algorithm": sig_info.algorithm,
                "public_key": sig_info.public_key,
                "signature": sig_info.signature,
            },
        )

        assert result.status == SignatureStatus.INVALID
        assert result.valid is False
        assert result.error is not None

    def test_verify_missing_public_key(self):
        """Should return INVALID when public_key missing."""
        verifier = Ed25519Verifier()

        result = verifier.verify(
            "content",
            {"signature": "some-signature"},
        )

        assert result.status == SignatureStatus.INVALID
        assert "Missing public_key" in result.error

    def test_verify_missing_signature(self):
        """Should return INVALID when signature missing."""
        verifier = Ed25519Verifier()

        result = verifier.verify(
            "content",
            {"public_key": "some-key"},
        )

        assert result.status == SignatureStatus.INVALID
        assert "Missing" in result.error

    def test_verify_parses_timestamp(self):
        """Should parse timestamp from signature info."""
        signer = Ed25519Signer.generate()
        verifier = Ed25519Verifier()
        content = "test content"

        sig_info = signer.sign(content, "test@example.com")
        result = verifier.verify(
            content,
            {
                "public_key": sig_info.public_key,
                "signature": sig_info.signature,
                "timestamp": "2024-01-15T12:00:00Z",
            },
        )

        assert result.timestamp == datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


class TestVerifierRegistry:
    """Tests for VerifierRegistry."""

    def test_register_and_get(self):
        """Should register and retrieve verifier."""
        registry = VerifierRegistry()
        verifier = Ed25519Verifier()

        registry.register(verifier)
        retrieved = registry.get("ed25519")

        assert retrieved is verifier

    def test_get_unknown_algorithm(self):
        """Should return None for unknown algorithm."""
        registry = VerifierRegistry()

        result = registry.get("unknown-algo")

        assert result is None

    def test_verify_routes_to_correct_verifier(self):
        """Should route to correct verifier based on algorithm."""
        signer = Ed25519Signer.generate()
        content = "test content"
        sig_info = signer.sign(content, "test@example.com")

        result = default_registry.verify(
            content,
            {
                "algorithm": "ed25519",
                "public_key": sig_info.public_key,
                "signature": sig_info.signature,
            },
        )

        assert result.status == SignatureStatus.VALID

    def test_verify_unknown_algorithm(self):
        """Should return INVALID for unknown algorithm."""
        result = default_registry.verify(
            "content",
            {"algorithm": "unknown-algo", "public_key": "key", "signature": "sig"},
        )

        assert result.status == SignatureStatus.INVALID
        assert "Unknown algorithm" in result.error

    def test_verify_missing_algorithm(self):
        """Should return INVALID when no algorithm specified."""
        result = default_registry.verify(
            "content",
            {"public_key": "key", "signature": "sig"},
        )

        assert result.status == SignatureStatus.INVALID
        assert "No algorithm" in result.error


class TestSignDossier:
    """Tests for sign_dossier function."""

    def test_adds_signature_to_frontmatter(self):
        """Should add signature to frontmatter."""
        signer = Ed25519Signer.generate()
        content = """---
title: Test
---

Body content here.
"""
        result = sign_dossier(content, signer, "test@example.com", "key-123")

        assert "signature:" in result
        assert "algorithm: ed25519" in result
        assert "public_key:" in result
        assert "signed_by: test@example.com" in result

    def test_preserves_existing_frontmatter(self):
        """Should preserve existing frontmatter fields."""
        signer = Ed25519Signer.generate()
        content = """---
title: My Title
version: "1.0.0"
status: stable
---

Body content.
"""
        result = sign_dossier(content, signer, "test@example.com")

        assert "title: My Title" in result
        assert "version: " in result  # frontmatter may reformat quotes
        assert "status: stable" in result


class TestVerifyDossierSignature:
    """Tests for verify_dossier_signature function."""

    def test_valid_signed_dossier(self):
        """Should return VALID for properly signed dossier."""
        signer = Ed25519Signer.generate()
        content = """---
title: Test
---

Body content here.
"""
        signed_content = sign_dossier(content, signer, "test@example.com")
        result = verify_dossier_signature(signed_content)

        assert result.status == SignatureStatus.VALID
        assert result.valid is True
        assert result.signed_by == "test@example.com"

    def test_unsigned_dossier(self):
        """Should return UNSIGNED for dossier without signature."""
        content = """---
title: Test
---

Body content here.
"""
        result = verify_dossier_signature(content)

        assert result.status == SignatureStatus.UNSIGNED
        assert result.valid is False

    def test_tampered_dossier(self):
        """Should return INVALID for tampered content."""
        signer = Ed25519Signer.generate()
        content = """---
title: Test
---

Original body content.
"""
        signed_content = sign_dossier(content, signer, "test@example.com")

        # Tamper with the body
        tampered_content = signed_content.replace("Original body content.", "Tampered body content.")

        result = verify_dossier_signature(tampered_content)

        assert result.status == SignatureStatus.INVALID
        assert result.valid is False


class TestSignatureVerificationResult:
    """Tests for SignatureVerificationResult dataclass."""

    def test_valid_property_true(self):
        """Should return True when status is VALID."""
        result = SignatureVerificationResult(status=SignatureStatus.VALID)
        assert result.valid is True

    def test_valid_property_false_invalid(self):
        """Should return False when status is INVALID."""
        result = SignatureVerificationResult(status=SignatureStatus.INVALID)
        assert result.valid is False

    def test_valid_property_false_unsigned(self):
        """Should return False when status is UNSIGNED."""
        result = SignatureVerificationResult(status=SignatureStatus.UNSIGNED)
        assert result.valid is False
