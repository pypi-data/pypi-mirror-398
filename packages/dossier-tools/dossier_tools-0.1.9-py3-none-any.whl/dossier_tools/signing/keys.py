"""Key storage and management for dossier signing."""

from __future__ import annotations

from pathlib import Path

from .ed25519 import Ed25519Signer


def get_dossier_dir() -> Path:
    """Return ~/.dossier directory path.

    Does not create the directory - use ensure_dossier_dir() for that.
    """
    return Path.home() / ".dossier"


def ensure_dossier_dir() -> Path:
    """Return ~/.dossier directory, creating if needed."""
    dossier_dir = get_dossier_dir()
    dossier_dir.mkdir(mode=0o700, exist_ok=True)
    return dossier_dir


def get_private_key_path(name: str = "default") -> Path:
    """Return path to private key file.

    Args:
        name: Key name (default: "default")

    Returns:
        Path to ~/.dossier/<name>.pem
    """
    return get_dossier_dir() / f"{name}.pem"


def get_public_key_path(name: str = "default") -> Path:
    """Return path to public key file.

    Args:
        name: Key name (default: "default")

    Returns:
        Path to ~/.dossier/<name>.pub
    """
    return get_dossier_dir() / f"{name}.pub"


def key_exists(name: str = "default") -> bool:
    """Check if a key pair exists.

    Args:
        name: Key name (default: "default")

    Returns:
        True if private key file exists
    """
    return get_private_key_path(name).exists()


def load_signer(name: str = "default") -> Ed25519Signer:
    """Load signer from stored key.

    Args:
        name: Key name (default: "default")

    Returns:
        Ed25519Signer instance

    Raises:
        FileNotFoundError: If key file doesn't exist
    """
    key_path = get_private_key_path(name)
    if not key_path.exists():
        msg = f"Key '{name}' not found at {key_path}"
        raise FileNotFoundError(msg)
    return Ed25519Signer.from_pem_file(key_path)


def save_key_pair(signer: Ed25519Signer, name: str = "default") -> tuple[Path, Path]:
    """Save key pair to storage.

    Args:
        signer: Ed25519Signer with key pair to save
        name: Key name (default: "default")

    Returns:
        Tuple of (private_key_path, public_key_path)
    """
    ensure_dossier_dir()

    private_path = get_private_key_path(name)
    public_path = get_public_key_path(name)

    # Write private key with restricted permissions
    private_path.write_text(signer.get_private_key_pem())
    private_path.chmod(0o600)

    # Write public key (readable)
    public_path.write_text(signer.get_public_key())
    public_path.chmod(0o644)

    return private_path, public_path


def list_keys() -> list[str]:
    """List all available key names.

    Returns:
        List of key names (without .pem extension)
    """
    dossier_dir = get_dossier_dir()
    if not dossier_dir.exists():
        return []
    return [p.stem for p in dossier_dir.glob("*.pem")]


__all__ = [
    "ensure_dossier_dir",
    "get_dossier_dir",
    "get_private_key_path",
    "get_public_key_path",
    "key_exists",
    "list_keys",
    "load_signer",
    "save_key_pair",
]
