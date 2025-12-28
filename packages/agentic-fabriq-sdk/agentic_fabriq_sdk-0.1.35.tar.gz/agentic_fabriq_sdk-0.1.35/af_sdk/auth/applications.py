"""
Authentication helpers for Agentic Fabric SDK.

Provides utilities for loading application credentials and creating
authenticated clients.
"""

from pathlib import Path
import json
import httpx
from typing import Optional, List, Dict, Tuple
import logging

from ..fabriq_client import FabriqClient

logger = logging.getLogger(__name__)


class ApplicationNotFoundError(Exception):
    """Raised when an application configuration is not found."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


async def get_application_client(
    app_id: str,
    config_dir: Optional[Path] = None,
    gateway_url: Optional[str] = None,
) -> FabriqClient:
    """
    Get authenticated FabriqClient for an application.
    
    Automatically loads credentials from ~/.af/applications/{app_id}.json
    and exchanges them for a JWT token.
    
    Args:
        app_id: Application identifier (e.g., "my-slack-bot")
        config_dir: Optional custom config directory (default: ~/.af)
        gateway_url: Optional gateway URL override (default: from app config)
    
    Returns:
        Authenticated FabriqClient instance
    
    Raises:
        ApplicationNotFoundError: If application config doesn't exist
        AuthenticationError: If authentication fails
    
    Example:
        >>> client = await get_application_client("my-slack-bot")
        >>> result = await client.invoke_connection("my-slack", method="post_message", parameters={...})
    """
    # 1. Load application config
    try:
        app_config = load_application_config(app_id, config_dir)
    except FileNotFoundError as e:
        raise ApplicationNotFoundError(
            f"Application '{app_id}' not found. "
            f"Register it first with: afctl applications create --app-id {app_id} ..."
        ) from e
    
    # Use provided gateway_url or fall back to config
    base_url = gateway_url or app_config.get("gateway_url", "https://dashboard.agenticfabriq.com")
    
    # 2. Exchange credentials for JWT token
    try:
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f"{base_url}/api/v1/applications/token",
                json={
                    "app_id": app_config["app_id"],
                    "secret_key": app_config["secret_key"]
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", response.text)
                except:
                    pass
                
                raise AuthenticationError(
                    f"Failed to authenticate application '{app_id}': {error_detail}"
                )
            
            token_data = response.json()
    except httpx.HTTPError as e:
        raise AuthenticationError(
            f"Network error while authenticating application '{app_id}': {e}"
        ) from e
    
    # 3. Create and return authenticated client
    client = FabriqClient(
        base_url=base_url,
        auth_token=token_data["access_token"]
    )
    
    # Store metadata for potential refresh
    client._app_id = app_id
    client._expires_in = token_data.get("expires_in", 86400)
    
    logger.info(
        f"Authenticated as application '{app_id}' "
        f"(user_id={token_data.get('user_id')}, tenant_id={token_data.get('tenant_id')})"
    )
    
    return client


async def register_application(
    app_id: str,
    provider_scopes: Dict[str, List[str]],
    auth_token: str,
    gateway_url: str = "https://dashboard.agenticfabriq.com",
    display_name: Optional[str] = None,
) -> Tuple[str, Dict]:
    """
    Register a new application (Step 1 of 2).
    
    This registers your application with the gateway and returns a temporary
    activation token that expires in 1 hour. Use this token with activate_application()
    to complete the setup.
    
    Args:
        app_id: Application identifier (no spaces)
        provider_scopes: Dict mapping provider names to list of scope names
                        e.g., {"slack": ["channels:read", "chat:write"]}
        auth_token: User JWT token for authentication
        gateway_url: Gateway URL (default: https://dashboard.agenticfabriq.com)
        display_name: Optional display name for the application
    
    Returns:
        Tuple of (activation_token, registration_data)
    
    Raises:
        AuthenticationError: If registration fails
    
    Example:
        >>> scopes = {
        ...     "slack": ["channels:read", "chat:write"],
        ...     "google": ["gmail.send"]
        ... }
        >>> token, data = await register_application(
        ...     "my-bot",
        ...     scopes,
        ...     auth_token="eyJ..."
        ... )
        >>> print(f"Activation token: {token}")
    """
    try:
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f"{gateway_url}/api/v1/applications/register",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "app_id": app_id,
                    "provider_scopes": provider_scopes,
                    "display_name": display_name,
                },
                timeout=30.0
            )
            
            if response.status_code != 201:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", response.text)
                except:
                    pass
                
                raise AuthenticationError(
                    f"Failed to register application '{app_id}': {error_detail}"
                )
            
            data = response.json()
            logger.info(f"Registered application '{app_id}', activation token expires: {data.get('expires_at')}")
            return data["activation_token"], data
            
    except httpx.HTTPError as e:
        raise AuthenticationError(
            f"Network error while registering application '{app_id}': {e}"
        ) from e


async def activate_application(
    activation_token: str,
    auth_token: str,
    gateway_url: str = "https://dashboard.agenticfabriq.com",
    config_dir: Optional[Path] = None,
    auto_save: bool = True,
    idp_client_id: Optional[str] = None,
    idp_client_secret: Optional[str] = None,
) -> Dict:
    """
    Activate an application (Step 2 of 2).
    
    Uses the activation token from register_application() to activate the application
    and optionally save credentials locally.
    
    Args:
        activation_token: Activation token from register_application()
        auth_token: User JWT token for authentication
        gateway_url: Gateway URL (default: https://dashboard.agenticfabriq.com)
        config_dir: Optional custom config directory (default: ~/.af)
        auto_save: Automatically save credentials to disk (default: True)
        idp_client_id: Optional IdP client ID for Keycloak Identity Provider
        idp_client_secret: Optional IdP client secret for Keycloak Identity Provider
    
    Returns:
        Application credentials dictionary containing:
        - app_id: Application identifier
        - secret_key: Application secret key
        - keycloak_client_id: Namespaced Keycloak client ID
        - user_id: Owner user ID
        - tenant_id: Tenant ID
        - organization_id: Organization ID
        - created_at: Creation timestamp
        - oauth_config: OAuth configuration (if available)
    
    Raises:
        AuthenticationError: If activation fails
    
    Example:
        >>> # After registering
        >>> credentials = await activate_application(
        ...     activation_token="act_...",
        ...     auth_token="eyJ..."
        ... )
        >>> print(f"App ID: {credentials['app_id']}")
        >>> print(f"Secret: {credentials['secret_key']}")
    """
    try:
        # Build request payload
        payload = {"activation_token": activation_token}
        if idp_client_id:
            payload["idp_client_id"] = idp_client_id
        if idp_client_secret:
            payload["idp_client_secret"] = idp_client_secret
        
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f"{gateway_url}/api/v1/applications/activate",
                headers={"Authorization": f"Bearer {auth_token}"},
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 404:
                raise AuthenticationError(
                    "Invalid or expired activation token. "
                    "The token may have expired (valid for 1 hour) or was already used."
                )
            elif response.status_code == 403:
                raise AuthenticationError("This activation token does not belong to you")
            elif response.status_code != 201:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", response.text)
                except:
                    pass
                
                raise AuthenticationError(f"Failed to activate application: {error_detail}")
            
            data = response.json()
            
            # Optionally save credentials locally
            if auto_save:
                app_config = {
                    "app_id": data["app_id"],
                    "secret_key": data["secret_key"],
                    "keycloak_client_id": data.get("keycloak_client_id"),
                    "user_id": data["user_id"],
                    "tenant_id": data["tenant_id"],
                    "organization_id": data.get("organization_id"),
                    "tool_connections": data.get("tool_connections", {}),
                    "created_at": data["created_at"],
                    "gateway_url": gateway_url
                }
                
                app_file = save_application_config(data["app_id"], app_config, config_dir)
                logger.info(f"Saved application credentials to {app_file}")
                data["_config_file"] = str(app_file)
            
            logger.info(f"Activated application '{data['app_id']}'")
            return data
            
    except httpx.HTTPError as e:
        raise AuthenticationError(
            f"Network error while activating application: {e}"
        ) from e


async def exchange_okta_for_af_token(
    okta_token: str,
    app_id: str,
    app_secret: str,
    keycloak_url: str = "https://stagingauth.agenticfabriq.com",
    keycloak_realm: str = "agentic-fabric",
    gateway_url: str = "https://staging.agenticfabriq.com",
) -> str:
    """
    Exchange Okta SSO token for AF JWT token.
    
    This function handles the complete flow for applications that use Okta SSO:
    1. Exchange Okta token for Keycloak token (RFC 8693)
    2. Exchange Keycloak token for AF JWT with full metadata
    
    The Keycloak Identity Provider alias is automatically derived as: {app_id}_idp
    For example, if app_id is "my-app", the IdP alias should be "my-app_idp" in Keycloak.
    
    Args:
        okta_token: User's Okta JWT from SSO flow (access_token or id_token)
        app_id: Application ID from afctl activation (same as Keycloak client_id)
        app_secret: Application secret from afctl activation (same as Keycloak client_secret)
        keycloak_url: Keycloak server URL
        keycloak_realm: Keycloak realm name
        gateway_url: AF Gateway URL
    
    Returns:
        AF JWT token containing user_id, tenant_id, organization_id, app_id, roles, and scopes
        
    Raises:
        AuthenticationError: If token exchange fails at any step
    
    Example:
        >>> # User SSO'd via Okta, app received Okta token
        >>> okta_token = "eyJhbGc..."
        >>> 
        >>> # Exchange for AF token (IdP alias auto-derived as "my-openwebui-app_idp")
        >>> af_token = await exchange_okta_for_af_token(
        ...     okta_token=okta_token,
        ...     app_id="my-openwebui-app",
        ...     app_secret="sk_abc123..."
        ... )
        >>> 
        >>> # Use AF token for MCP calls
        >>> from af_sdk import FabriqClient
        >>> client = FabriqClient(auth_token=af_token)
    
    Note:
        When creating the Okta Identity Provider in Keycloak, use the alias: {app_id}_idp
        For app_id "my-app", create IdP with alias "my-app_idp"
    """
    # Automatically derive IdP alias from app_id
    keycloak_idp_alias = f"{app_id}_idp"
    logger.debug(f"Using derived IdP alias: {keycloak_idp_alias}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as http:
            # Step 1: Okta → Keycloak (RFC 8693 Token Exchange)
            logger.info(f"Exchanging Okta token for Keycloak token via IdP: {keycloak_idp_alias}")
            keycloak_response = await http.post(
                f"{keycloak_url}/realms/{keycloak_realm}/protocol/openid-connect/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "subject_token": okta_token,
                    "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "subject_issuer": keycloak_idp_alias,
                    "audience": app_id,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if keycloak_response.status_code != 200:
                error_detail = keycloak_response.text
                logger.error(f"Keycloak token exchange failed: {error_detail}")
                raise AuthenticationError(
                    f"Keycloak token exchange failed (status {keycloak_response.status_code}): {error_detail}"
                )
            
            keycloak_token = keycloak_response.json()["access_token"]
            logger.info("Successfully obtained Keycloak token")
            
            # Step 2: Keycloak → AF (Enrich with metadata + app_id)
            logger.info("Exchanging Keycloak token for AF JWT")
            af_response = await http.post(
                f"{gateway_url}/api/v1/auth/keycloak-token-exchange",
                headers={
                    "Authorization": f"Bearer {keycloak_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "app_id": app_id,
                    "app_secret": app_secret
                }
            )
            
            if af_response.status_code != 200:
                error_detail = af_response.text
                logger.error(f"AF token exchange failed: {error_detail}")
                raise AuthenticationError(
                    f"AF token exchange failed (status {af_response.status_code}): {error_detail}"
                )
            
            af_token = af_response.json()["access_token"]
            logger.info("Successfully obtained AF JWT token")
            
            return af_token
            
    except httpx.RequestError as e:
        logger.error(f"Network error during token exchange: {e}")
        raise AuthenticationError(f"Token exchange network error: {str(e)}") from e
    except KeyError as e:
        logger.error(f"Invalid token response format: {e}")
        raise AuthenticationError(f"Invalid token response format: {str(e)}") from e


def load_application_config(
    app_id: str,
    config_dir: Optional[Path] = None
) -> Dict:
    """
    Load application config from disk.
    
    Args:
        app_id: Application identifier
        config_dir: Optional custom config directory (default: ~/.af)
    
    Returns:
        Application configuration dictionary
    
    Raises:
        FileNotFoundError: If application config doesn't exist
    
    Example:
        >>> config = load_application_config("my-slack-bot")
        >>> print(config["app_id"], config["created_at"])
    """
    if config_dir is None:
        config_dir = Path.home() / ".af"
    
    app_file = config_dir / "applications" / f"{app_id}.json"
    
    if not app_file.exists():
        raise FileNotFoundError(
            f"Application '{app_id}' not found at {app_file}. "
            f"Register it with: afctl applications create --app-id {app_id}"
        )
    
    with open(app_file, "r") as f:
        return json.load(f)


def save_application_config(
    app_id: str,
    config: Dict,
    config_dir: Optional[Path] = None
) -> Path:
    """
    Save application config to disk.
    
    Args:
        app_id: Application identifier
        config: Application configuration dictionary
        config_dir: Optional custom config directory (default: ~/.af)
    
    Returns:
        Path to saved config file
    
    Example:
        >>> config = {
        ...     "app_id": "my-bot",
        ...     "secret_key": "sk_...",
        ...     "gateway_url": "https://dashboard.agenticfabriq.com"
        ... }
        >>> path = save_application_config("my-bot", config)
    """
    if config_dir is None:
        config_dir = Path.home() / ".af"
    
    # Create applications directory if it doesn't exist
    app_dir = config_dir / "applications"
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # Write config file
    app_file = app_dir / f"{app_id}.json"
    with open(app_file, "w") as f:
        json.dump(config, f, indent=2)
    
    # Secure the file (user read/write only)
    app_file.chmod(0o600)
    
    logger.info(f"Saved application config to {app_file}")
    
    return app_file


def list_applications(
    config_dir: Optional[Path] = None
) -> List[Dict]:
    """
    List all registered applications.
    
    Args:
        config_dir: Optional custom config directory (default: ~/.af)
    
    Returns:
        List of application configuration dictionaries
    
    Example:
        >>> apps = list_applications()
        >>> for app in apps:
        ...     print(f"{app['app_id']}: {app.get('name', 'N/A')}")
    """
    if config_dir is None:
        config_dir = Path.home() / ".af"
    
    app_dir = config_dir / "applications"
    
    if not app_dir.exists():
        return []
    
    apps = []
    for app_file in sorted(app_dir.glob("*.json")):
        try:
            with open(app_file, "r") as f:
                app_config = json.load(f)
                apps.append(app_config)
        except Exception as e:
            logger.warning(f"Failed to load application config from {app_file}: {e}")
    
    return apps


def delete_application_config(
    app_id: str,
    config_dir: Optional[Path] = None
) -> bool:
    """
    Delete application config from disk.
    
    Args:
        app_id: Application identifier
        config_dir: Optional custom config directory (default: ~/.af)
    
    Returns:
        True if deleted, False if not found
    
    Example:
        >>> deleted = delete_application_config("my-old-bot")
        >>> if deleted:
        ...     print("Deleted successfully")
    """
    if config_dir is None:
        config_dir = Path.home() / ".af"
    
    app_file = config_dir / "applications" / f"{app_id}.json"
    
    if not app_file.exists():
        return False
    
    app_file.unlink()
    logger.info(f"Deleted application config: {app_file}")
    
    return True

