"""
Authentication and authorization utilities for Agentic Fabric SDK.
"""

from .oauth import (
    api_key_required,
    mtls_required,
    no_auth_required,
    oauth_required,
    ScopeValidator,
    TokenValidator,
)
from .token_cache import TokenManager, VaultClient
from .applications import (
    get_application_client,
    register_application,
    activate_application,
    exchange_okta_for_af_token,
    load_application_config,
    save_application_config,
    list_applications,
    delete_application_config,
    ApplicationNotFoundError,
    AuthenticationError,
)
from .credentials import (
    load_stored_credentials,
    exchange_keycloak_for_af_token,
    get_valid_token_sync,
    StoredCredentials,
    AFTokenResponse,
)

# DPoP helper will be provided from af_sdk.auth.dpop
try:
    from .dpop import create_dpop_proof
except Exception:  # pragma: no cover - optional import if file missing
    create_dpop_proof = None  # type: ignore

__all__ = [
    "oauth_required",
    "api_key_required",
    "mtls_required",
    "no_auth_required",
    "ScopeValidator",
    "TokenValidator",
    "TokenManager",
    "VaultClient",
    "create_dpop_proof",
    "get_application_client",
    "register_application",
    "activate_application",
    "exchange_okta_for_af_token",
    "load_application_config",
    "save_application_config",
    "list_applications",
    "delete_application_config",
    "ApplicationNotFoundError",
    "AuthenticationError",
    # Non-IdP authentication
    "load_stored_credentials",
    "exchange_keycloak_for_af_token",
    "get_valid_token_sync",
    "StoredCredentials",
    "AFTokenResponse",
] 