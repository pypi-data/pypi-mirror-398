"""Base classes and types for signing implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime  # noqa: TC003 - used at runtime in dataclass
from enum import Enum
from typing import Any


class SignatureStatus(Enum):
    """Status of signature verification."""

    VALID = "valid"  # Signature is cryptographically valid
    INVALID = "invalid"  # Signature doesn't match
    UNSIGNED = "unsigned"  # No signature present


@dataclass
class SignatureInfo:
    """Signature metadata for frontmatter."""

    algorithm: str
    public_key: str  # Base64 encoded
    signature: str  # Base64 encoded
    signed_by: str
    timestamp: datetime
    key_id: str | None = None


@dataclass
class SignatureVerificationResult:
    """Result of signature verification."""

    status: SignatureStatus
    algorithm: str | None = None
    signed_by: str | None = None
    timestamp: datetime | None = None
    error: str | None = None

    @property
    def valid(self) -> bool:
        """Return True if signature is valid."""
        return self.status == SignatureStatus.VALID


class Signer(ABC):
    """Abstract base class for signing content."""

    @property
    @abstractmethod
    def algorithm(self) -> str:
        """Return the algorithm identifier (e.g., 'ed25519')."""
        ...

    @abstractmethod
    def sign(
        self,
        content: str,
        signed_by: str,
        key_id: str | None = None,
    ) -> SignatureInfo:
        """Sign content and return signature info."""
        ...

    @abstractmethod
    def get_public_key(self) -> str:
        """Return base64-encoded public key."""
        ...


class Verifier(ABC):
    """Abstract base class for verifying signatures."""

    @property
    @abstractmethod
    def algorithm(self) -> str:
        """Return the algorithm identifier this verifier handles."""
        ...

    @abstractmethod
    def verify(self, content: str, signature_info: dict[str, Any]) -> SignatureVerificationResult:
        """Verify signature and return result."""
        ...


__all__ = [
    "SignatureInfo",
    "SignatureStatus",
    "SignatureVerificationResult",
    "Signer",
    "Verifier",
]
