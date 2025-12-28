"""Registry client for interacting with dossier registries."""

from .auth import (
    Credentials,
    delete_credentials,
    delete_token,
    get_credentials_path,
    get_token_path,
    load_credentials,
    load_token,
    save_credentials,
    save_token,
)
from .client import (
    RegistryClient,
    RegistryError,
    get_client,
    get_registry_url,
    parse_name_version,
)
from .oauth import OAuthError, OAuthResult, run_oauth_flow

__all__ = [
    "Credentials",
    "OAuthError",
    "OAuthResult",
    "RegistryClient",
    "RegistryError",
    "delete_credentials",
    "delete_token",
    "get_client",
    "get_credentials_path",
    "get_registry_url",
    "get_token_path",
    "load_credentials",
    "load_token",
    "parse_name_version",
    "run_oauth_flow",
    "save_credentials",
    "save_token",
]
