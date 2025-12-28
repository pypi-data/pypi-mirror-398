"""Signing and verification for dossier files."""

from __future__ import annotations

import frontmatter as fm

from ..core.parser import parse_content
from .base import (
    SignatureInfo,
    SignatureStatus,
    SignatureVerificationResult,
    Signer,
    Verifier,
)
from .keys import (
    ensure_dossier_dir,
    get_dossier_dir,
    get_private_key_path,
    get_public_key_path,
    key_exists,
    list_keys,
    load_signer,
    save_key_pair,
)


def sign_dossier(
    content: str,
    signer: Signer,
    signed_by: str,
    key_id: str | None = None,
) -> str:
    """Sign a dossier and return updated content with signature in frontmatter.

    Args:
        content: Raw .ds.md file content
        signer: Signer instance to use
        signed_by: Identity of signer (e.g., email)
        key_id: Optional key identifier

    Returns:
        Content with signature added to frontmatter
    """
    parsed = parse_content(content)
    sig_info = signer.sign(parsed.body, signed_by, key_id)

    # Add signature to frontmatter
    parsed.frontmatter["signature"] = {
        "algorithm": sig_info.algorithm,
        "public_key": sig_info.public_key,
        "signature": sig_info.signature,
        "signed_by": sig_info.signed_by,
        "timestamp": sig_info.timestamp.isoformat(),
    }
    if sig_info.key_id:
        parsed.frontmatter["signature"]["key_id"] = sig_info.key_id

    post = fm.Post(parsed.body, **parsed.frontmatter)
    return fm.dumps(post)


def verify_dossier_signature(content: str) -> SignatureVerificationResult:
    """Verify signature of a dossier.

    Args:
        content: Raw .ds.md file content

    Returns:
        SignatureVerificationResult with status and details
    """
    # Lazy import: registry.py instantiates Ed25519Verifier at module level,
    # so we defer loading until verification is actually needed.
    from .registry import verify_signature  # noqa: PLC0415

    parsed = parse_content(content)
    signature_info = parsed.frontmatter.get("signature")

    if not signature_info:
        return SignatureVerificationResult(status=SignatureStatus.UNSIGNED)

    return verify_signature(parsed.body, signature_info)


__all__ = [
    # base
    "SignatureInfo",
    "SignatureStatus",
    "SignatureVerificationResult",
    "Signer",
    "Verifier",
    # keys
    "ensure_dossier_dir",
    "get_dossier_dir",
    "get_private_key_path",
    "get_public_key_path",
    "key_exists",
    "list_keys",
    "load_signer",
    "save_key_pair",
    # functions
    "sign_dossier",
    "verify_dossier_signature",
]
