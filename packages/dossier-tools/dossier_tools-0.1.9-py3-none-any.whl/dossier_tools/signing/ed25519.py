"""Ed25519 signing and verification."""

from __future__ import annotations

import base64
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from ..logging import get_logger
from .base import (
    SignatureInfo,
    SignatureStatus,
    SignatureVerificationResult,
    Signer,
    Verifier,
)

logger = get_logger("signing")


class Ed25519Signer(Signer):
    """Sign content using Ed25519."""

    def __init__(self, private_key: Ed25519PrivateKey):
        """Initialize with an Ed25519 private key.

        Args:
            private_key: Ed25519 private key instance
        """
        self._private_key = private_key
        self._public_key = private_key.public_key()

    @classmethod
    def from_pem_file(cls, path: Path | str) -> Ed25519Signer:
        """Load signer from PEM file.

        Args:
            path: Path to PEM file containing Ed25519 private key

        Returns:
            Ed25519Signer instance

        Raises:
            ValueError: If file doesn't contain an Ed25519 private key
            FileNotFoundError: If file doesn't exist
        """
        path = Path(path).expanduser()
        logger.debug("Loading key from: %s", path)
        pem_data = path.read_bytes()
        private_key = serialization.load_pem_private_key(pem_data, password=None)
        if not isinstance(private_key, Ed25519PrivateKey):
            msg = "Not an Ed25519 private key"
            raise TypeError(msg)
        return cls(private_key)

    @classmethod
    def from_env(cls, var_name: str = "DOSSIER_SIGNING_KEY") -> Ed25519Signer:
        """Load signer from environment variable.

        The environment variable can contain either:
        - PEM-encoded private key (starts with '-----')
        - Base64-encoded raw private key bytes

        Args:
            var_name: Name of environment variable

        Returns:
            Ed25519Signer instance

        Raises:
            ValueError: If environment variable not set or invalid
        """
        value = os.environ.get(var_name)
        if not value:
            msg = f"Environment variable {var_name} not set"
            raise ValueError(msg)

        # Try PEM first, then base64
        if value.startswith("-----"):
            private_key = serialization.load_pem_private_key(value.encode(), password=None)
        else:
            key_bytes = base64.b64decode(value)
            private_key = Ed25519PrivateKey.from_private_bytes(key_bytes)

        if not isinstance(private_key, Ed25519PrivateKey):
            msg = "Not an Ed25519 private key"
            raise TypeError(msg)

        return cls(private_key)

    @classmethod
    def generate(cls) -> Ed25519Signer:
        """Generate a new Ed25519 key pair.

        Returns:
            Ed25519Signer instance with newly generated key
        """
        logger.debug("Generating new Ed25519 key pair")
        private_key = Ed25519PrivateKey.generate()
        return cls(private_key)

    @property
    def algorithm(self) -> str:
        """Return the algorithm identifier."""
        return "ed25519"

    def get_public_key(self) -> str:
        """Return base64-encoded public key."""
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(public_bytes).decode()

    def get_private_key_pem(self) -> str:
        """Return PEM-encoded private key.

        Useful for saving the key to a file.
        """
        pem_bytes = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return pem_bytes.decode()

    def sign(
        self,
        content: str,
        signed_by: str,
        key_id: str | None = None,
    ) -> SignatureInfo:
        """Sign content and return signature info.

        Args:
            content: Content to sign
            signed_by: Identity of signer (e.g., email)
            key_id: Optional key identifier

        Returns:
            SignatureInfo with signature details
        """
        logger.debug("Signing content (%d bytes) as %s", len(content), signed_by)
        signature = self._private_key.sign(content.encode("utf-8"))
        logger.info("Signed by: %s", signed_by)
        return SignatureInfo(
            algorithm=self.algorithm,
            public_key=self.get_public_key(),
            signature=base64.b64encode(signature).decode(),
            signed_by=signed_by,
            timestamp=datetime.now(UTC),
            key_id=key_id,
        )


class Ed25519Verifier(Verifier):
    """Verify Ed25519 signatures."""

    @property
    def algorithm(self) -> str:
        """Return the algorithm identifier this verifier handles."""
        return "ed25519"

    def verify(self, content: str, signature_info: dict[str, Any]) -> SignatureVerificationResult:
        """Verify signature and return result.

        Args:
            content: Content that was signed
            signature_info: Dict with public_key, signature, and other metadata

        Returns:
            SignatureVerificationResult with status and details
        """
        logger.debug("Verifying signature")
        try:
            public_key_b64 = signature_info.get("public_key")
            signature_b64 = signature_info.get("signature")

            if not public_key_b64 or not signature_b64:
                logger.warning("Missing public_key or signature")
                return SignatureVerificationResult(
                    status=SignatureStatus.INVALID,
                    error="Missing public_key or signature",
                )

            public_bytes = base64.b64decode(public_key_b64)
            signature_bytes = base64.b64decode(signature_b64)

            public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
            public_key.verify(signature_bytes, content.encode("utf-8"))

            # Parse timestamp if present
            timestamp = None
            if ts := signature_info.get("timestamp"):
                timestamp = datetime.fromisoformat(ts)

            signed_by = signature_info.get("signed_by")
            logger.info("Signature valid (signed by: %s)", signed_by)
            return SignatureVerificationResult(
                status=SignatureStatus.VALID,
                algorithm=self.algorithm,
                signed_by=signed_by,
                timestamp=timestamp,
            )
        except InvalidSignature:
            logger.warning("Signature verification failed: invalid signature")
            return SignatureVerificationResult(
                status=SignatureStatus.INVALID,
                error="Invalid signature",
            )
        except (ValueError, TypeError) as e:
            logger.warning("Signature verification failed: %s", e)
            return SignatureVerificationResult(
                status=SignatureStatus.INVALID,
                error=str(e),
            )


__all__ = [
    "Ed25519Signer",
    "Ed25519Verifier",
]
