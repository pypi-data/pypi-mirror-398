"""
Credentials management for non-IdP authentication flows.

This module provides functions for:
1. Loading stored credentials from CLI login (afctl auth login)
2. Exchanging Keycloak tokens for app-scoped AF tokens

These functions are used by:
- Individual users who authenticate via CLI
- Organizations without external IdP (using Keycloak directly)
"""

import time
from pathlib import Path
from typing import Optional
import httpx
from pydantic import BaseModel

from .applications import AuthenticationError


class StoredCredentials(BaseModel):
    """Credentials stored by 'afctl auth login'."""
    
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: int  # Unix timestamp
    tenant_id: Optional[str] = None
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if the token is expired (with 60s buffer)."""
        return time.time() >= (self.expires_at - 60)
    
    @property
    def expires_in(self) -> int:
        """Seconds until token expires."""
        remaining = self.expires_at - int(time.time())
        return max(0, remaining)


class AFTokenResponse(BaseModel):
    """Response from AF token exchange."""
    
    access_token: str
    expires_in: int
    token_type: str = "Bearer"
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    organization_id: Optional[str] = None
    app_id: Optional[str] = None


def load_stored_credentials() -> Optional[StoredCredentials]:
    """
    Load Keycloak credentials saved by 'afctl auth login'.
    
    The credentials are stored securely in ~/.af/ using system keychain
    or encrypted file storage.
    
    Returns:
        StoredCredentials if available, None if not logged in
        
    Example:
        >>> creds = load_stored_credentials()
        >>> if creds is None:
        ...     print("Please run 'afctl auth login' first")
        >>> elif creds.is_expired:
        ...     print("Token expired, please run 'afctl auth login' again")
        >>> else:
        ...     print(f"Logged in as {creds.email}")
    """
    try:
        # Import TokenStorage from CLI module
        # This reuses the same storage mechanism as the CLI
        from af_cli.core.token_storage import TokenStorage, TokenData
        
        storage = TokenStorage()
        token_data: Optional[TokenData] = storage.load()
        
        if token_data is None:
            return None
        
        return StoredCredentials(
            access_token=token_data.access_token,
            refresh_token=token_data.refresh_token,
            expires_at=token_data.expires_at,
            tenant_id=token_data.tenant_id,
            organization_id=token_data.organization_id,
            user_id=token_data.user_id,
            email=token_data.email,
            name=token_data.name,
        )
    except ImportError:
        # CLI module not available - check for file directly
        config_dir = Path.home() / ".af"
        if not config_dir.exists():
            return None
        
        # Try to load from encrypted file (requires CLI to be installed)
        return None
    except Exception:
        return None


async def exchange_keycloak_for_af_token(
    keycloak_token: str,
    app_id: str,
    secret_key: str,
    gateway_url: str = "https://dashboard.agenticfabriq.com",
) -> AFTokenResponse:
    """
    Exchange a Keycloak token for an app-scoped AF token.
    
    This function is used by non-IdP users to get a JWT that includes:
    - User identity (from Keycloak token)
    - App context (from app_id)
    - Scopes for MCP tool access
    
    Args:
        keycloak_token: Keycloak access token (from CLI login or OAuth flow)
        app_id: Application ID (e.g., "org-xxx_myapp")
        secret_key: Application secret key
        gateway_url: Gateway URL (default: production)
    
    Returns:
        AFTokenResponse with app-scoped JWT for MCP calls
        
    Raises:
        AuthenticationError: If token exchange fails
        
    Example:
        >>> # Individual user with CLI login
        >>> creds = load_stored_credentials()
        >>> if creds and not creds.is_expired:
        ...     af_token = await exchange_keycloak_for_af_token(
        ...         keycloak_token=creds.access_token,
        ...         app_id="myapp",
        ...         secret_key="sk_xxx..."
        ...     )
        ...     # Use af_token.access_token with MCP
        
        >>> # Org without IdP (Keycloak OAuth flow)
        >>> af_token = await exchange_keycloak_for_af_token(
        ...     keycloak_token=keycloak_token_from_oauth,
        ...     app_id="org-xxx_myapp",
        ...     secret_key="sk_xxx..."
        ... )
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{gateway_url}/api/v1/applications/token",
                json={
                    "app_id": app_id,
                    "secret_key": secret_key,
                    "user_token": keycloak_token,
                },
                timeout=30.0,
            )
            
            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid app credentials or user token"
                )
            elif response.status_code == 403:
                raise AuthenticationError(
                    "User not authorized for this application"
                )
            elif response.status_code != 200:
                error_detail = response.text
                raise AuthenticationError(
                    f"Token exchange failed (status {response.status_code}): {error_detail}"
                )
            
            data = response.json()
            
            return AFTokenResponse(
                access_token=data["access_token"],
                expires_in=data.get("expires_in", 3600),
                token_type=data.get("token_type", "Bearer"),
                user_id=data.get("user_id"),
                tenant_id=data.get("tenant_id"),
                organization_id=data.get("organization_id"),
                app_id=data.get("app_id"),
            )
            
        except httpx.RequestError as e:
            raise AuthenticationError(f"Failed to connect to gateway: {e}")


def get_valid_token_sync(
    app_id: str,
    secret_key: str,
    gateway_url: str = "https://dashboard.agenticfabriq.com",
) -> str:
    """
    Synchronous helper to get a valid AF token using stored credentials.
    
    Combines load_stored_credentials() and exchange_keycloak_for_af_token()
    into a single synchronous call for convenience.
    
    Args:
        app_id: Application ID
        secret_key: Application secret key
        gateway_url: Gateway URL
    
    Returns:
        AF access token string
        
    Raises:
        AuthenticationError: If not logged in, token expired, or exchange fails
        
    Example:
        >>> token = get_valid_token_sync("myapp", "sk_xxx...")
        >>> # Use token with MCP client
    """
    import asyncio
    
    creds = load_stored_credentials()
    
    if creds is None:
        raise AuthenticationError(
            "Not logged in. Please run 'afctl auth login' first."
        )
    
    if creds.is_expired:
        raise AuthenticationError(
            "Token expired. Please run 'afctl auth login' again."
        )
    
    # Run async exchange in sync context
    loop = asyncio.new_event_loop()
    try:
        af_token = loop.run_until_complete(
            exchange_keycloak_for_af_token(
                keycloak_token=creds.access_token,
                app_id=app_id,
                secret_key=secret_key,
                gateway_url=gateway_url,
            )
        )
        return af_token.access_token
    finally:
        loop.close()

