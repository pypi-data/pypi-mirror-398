"""Verifier registry for routing verification by algorithm."""

from __future__ import annotations

from typing import Any

from .base import SignatureStatus, SignatureVerificationResult, Verifier
from .ed25519 import Ed25519Verifier


class VerifierRegistry:
    """Registry of signature verifiers by algorithm."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._verifiers: dict[str, Verifier] = {}

    def register(self, verifier: Verifier) -> None:
        """Register a verifier for its algorithm.

        Args:
            verifier: Verifier instance to register
        """
        self._verifiers[verifier.algorithm] = verifier

    def get(self, algorithm: str) -> Verifier | None:
        """Get verifier for algorithm.

        Args:
            algorithm: Algorithm identifier (e.g., 'ed25519')

        Returns:
            Verifier instance or None if not found
        """
        return self._verifiers.get(algorithm)

    def verify(self, content: str, signature_info: dict[str, Any]) -> SignatureVerificationResult:
        """Verify using appropriate verifier based on algorithm.

        Args:
            content: Content that was signed
            signature_info: Dict with algorithm and signature details

        Returns:
            SignatureVerificationResult with status and details
        """
        algorithm = signature_info.get("algorithm")
        if not algorithm:
            return SignatureVerificationResult(
                status=SignatureStatus.INVALID,
                error="No algorithm specified in signature",
            )

        verifier = self.get(algorithm)
        if not verifier:
            return SignatureVerificationResult(
                status=SignatureStatus.INVALID,
                error=f"Unknown algorithm: {algorithm}",
            )

        return verifier.verify(content, signature_info)


# Default registry with Ed25519
default_registry = VerifierRegistry()
default_registry.register(Ed25519Verifier())


def verify_signature(content: str, signature_info: dict[str, Any]) -> SignatureVerificationResult:
    """Verify signature using default registry.

    Args:
        content: Content that was signed
        signature_info: Dict with algorithm and signature details

    Returns:
        SignatureVerificationResult with status and details
    """
    return default_registry.verify(content, signature_info)


__all__ = [
    "VerifierRegistry",
    "default_registry",
    "verify_signature",
]
