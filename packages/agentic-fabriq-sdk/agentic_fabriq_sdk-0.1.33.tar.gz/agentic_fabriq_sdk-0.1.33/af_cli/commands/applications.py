"""
CLI commands for managing registered applications.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

from af_cli.core.config import get_config
from af_cli.core.output import print_output

app = typer.Typer(help="Manage registered applications")
console = Console()


@app.command("register")
def register_application_cmd(
    app_id: str = typer.Option(..., "--app-id", help="Application identifier (no spaces)"),
    scopes: str = typer.Option(..., "--scopes", help="Scopes (format: 'provider:scope1,provider:scope2')"),
    display_name: Optional[str] = typer.Option(None, "--display-name", help="Display name for the application"),
):
    """
    Step 1: Register a new application (returns activation token).
    
    This registers your application and returns a temporary activation token
    that expires in 1 hour. Use this token with 'afctl applications connect'
    to complete the setup and save credentials locally.
    
    Example:
        afctl applications register \\
            --app-id my-slack-bot \\
            --scopes slack:channels:read,slack:chat:write,google:gmail.send \\
            --display-name "My Slack Bot"
    """
    config = get_config()
    
    if not config.is_authenticated():
        console.print("❌ Not authenticated. Run 'afctl auth login' first.", style="red")
        raise typer.Exit(1)
    
    # Parse scopes into provider_scopes dict
    provider_scopes = {}
    if scopes:
        for scope_item in scopes.split(","):
            try:
                provider, scope_name = scope_item.strip().split(":", 1)
                if provider not in provider_scopes:
                    provider_scopes[provider] = []
                provider_scopes[provider].append(scope_name)
            except ValueError:
                console.print(f"❌ Invalid scope format: '{scope_item}'. Use 'provider:scope'", style="red")
                raise typer.Exit(1)
    
    if not provider_scopes:
        console.print("❌ At least one scope is required", style="red")
        raise typer.Exit(1)
    
    # Use SDK function
    async def _register():
        from af_sdk import register_application, AuthenticationError
        
        try:
            activation_token, data = await register_application(
                app_id=app_id,
                provider_scopes=provider_scopes,
                auth_token=config.access_token,
                gateway_url=config.gateway_url,
                display_name=display_name,
            )
            
            # Display activation token
            console.print("\n✅ Application registered successfully!", style="green bold")
            console.print(f"\n📋 App ID: {data['app_id']}", style="cyan")
            if display_name:
                console.print(f"📝 Display Name: {display_name}", style="cyan")
            console.print(f"\n🔑 Activation Token:", style="yellow bold")
            console.print(f"   {activation_token}", style="yellow")
            console.print(f"\n⏰ Token expires: {data['expires_at'][:19]} UTC", style="white")
            console.print(f"   (Valid for 1 hour)", style="dim")
            
            console.print("\n📋 Next Steps:", style="cyan bold")
            console.print(f"   1. Navigate to your project directory", style="white")
            console.print(f"   2. Make sure you're authenticated: afctl auth login", style="white")
            console.print(f"   3. Run the activate command:", style="white")
            console.print(f"\n      afctl applications activate --app-id {app_id} --token {activation_token[:20]}...", style="green")
            console.print(f"\n⚠️  Save the activation token! It expires in 1 hour and can only be used once.", style="yellow bold")
            
        except AuthenticationError as e:
            console.print(f"❌ {e}", style="red")
            raise typer.Exit(1)

    asyncio.run(_register())


@app.command("activate")
def activate_application_cmd(
    app_id: str = typer.Option(..., "--app-id", help="Application identifier"),
    token: str = typer.Option(..., "--token", help="Activation token from registration"),
    idp_client_id: str = typer.Option(None, "--idp-client-id", help="IdP Client ID (from Okta app)"),
    idp_client_secret: str = typer.Option(None, "--idp-client-secret", help="IdP Client Secret (from Okta app)"),
    skip_idp: bool = typer.Option(False, "--skip-idp", help="Skip IdP configuration prompts"),
):
    """
    Step 2: Activate an application (saves credentials locally).
    
    Uses the activation token from the UI or 'afctl applications register' to activate
    the application and save credentials to the current directory.
    
    If your organization has SSO configured, you'll be prompted for IdP credentials
    to enable token exchange. You can find these in your Okta application settings.
    
    Example:
        afctl applications activate --app-id my-slack-bot --token <activation-token>
        
        # With IdP credentials:
        afctl applications activate --app-id my-bot --token <token> \\
            --idp-client-id 0oa... --idp-client-secret <secret>
    """
    config = get_config()
    
    if not config.is_authenticated():
        console.print("❌ Not authenticated. Run 'afctl auth login' first.", style="red")
        raise typer.Exit(1)
    
    # Prompt for IdP credentials if not provided and not skipped
    final_idp_client_id = idp_client_id
    final_idp_client_secret = idp_client_secret
    
    if not skip_idp and not (idp_client_id and idp_client_secret):
        console.print("\n🔐 [bold]IdP Configuration (for SSO/Token Exchange)[/bold]")
        console.print("   If your organization uses Okta SSO, enter the credentials from your Okta app.")
        console.print("   Press Enter to skip if not using SSO.\n")
        
        if not idp_client_id:
            final_idp_client_id = typer.prompt(
                "   IdP Client ID",
                default="",
                show_default=False,
            ).strip() or None
        
        if final_idp_client_id and not idp_client_secret:
            final_idp_client_secret = typer.prompt(
                "   IdP Client Secret",
                default="",
                show_default=False,
                hide_input=True,
            ).strip() or None
    
    # Use SDK function
    async def _activate():
        from af_sdk import activate_application, AuthenticationError
        
        try:
            data = await activate_application(
                activation_token=token,
                auth_token=config.access_token,
                gateway_url=config.gateway_url,
                auto_save=True,  # Automatically saves to ~/.af/applications/
                idp_client_id=final_idp_client_id,
                idp_client_secret=final_idp_client_secret,
            )
            
            # Display success
            console.print("\n✅ Application activated successfully!", style="green bold")
            console.print(f"\n📋 App ID: {data['app_id']}", style="cyan")
            if data.get('keycloak_client_id'):
                console.print(f"🔗 Keycloak Client ID: {data['keycloak_client_id']}", style="cyan")
            if data.get('display_name'):
                console.print(f"📝 Display Name: {data['display_name']}", style="cyan")
            console.print(f"🔑 Secret Key: {data['secret_key']}", style="yellow")
            
            # Show IdP info if configured
            if data.get('oauth_config', {}).get('idp_alias'):
                console.print(f"🔐 IdP Alias: {data['oauth_config']['idp_alias']}", style="cyan")
            
            if "_config_file" in data:
                console.print(f"\n💾 Credentials saved to: {data['_config_file']}", style="green")
            
            console.print("\n⚠️  Save the secret key securely! It won't be shown again.", style="yellow bold")
            console.print("\n🚀 Your agent can now authenticate with:", style="cyan")
            console.print(f"   from af_sdk import get_application_client", style="white")
            console.print(f"   client = await get_application_client('{data['app_id']}')", style="white")
            
        except AuthenticationError as e:
            console.print(f"❌ {e}", style="red")
            raise typer.Exit(1)
    
    asyncio.run(_activate())


# Backward compatibility alias
@app.command("connect", hidden=True)
def connect_application_alias(
    app_id: str = typer.Argument(..., help="Application identifier"),
    token: str = typer.Option(..., "--token", help="Activation token from registration"),
):
    """
    (Deprecated: use 'activate' instead)
    """
    console.print("⚠️  'connect' is deprecated. Use 'afctl applications activate' instead.", style="yellow")
    # Call the new activate command
    activate_application_cmd(app_id=app_id, token=token, skip_idp=True)


@app.command("list")
def list_applications(
    format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
    sync: bool = typer.Option(True, "--sync/--no-sync", help="Sync with server and remove orphaned local files"),
):
    """
    List all registered applications.
    
    Shows applications from local config files (~/.af/applications/) and optionally
    syncs with the server to remove any local files for applications that have been
    deleted from the server (e.g., via the UI).
    """
    config = get_config()
    
    # Load from local config first
    from af_sdk import list_applications as list_local_apps, delete_application_config
    
    local_apps = list_local_apps()
    
    # If sync is enabled and user is authenticated, check server and clean up orphans
    if sync and config.is_authenticated():
        try:
            response = httpx.get(
                f"{config.gateway_url}/api/v1/applications",
                headers={"Authorization": f"Bearer {config.access_token}"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                server_apps = data.get("applications", [])
                server_app_ids = {app["app_id"] for app in server_apps}
                
                # Find and remove orphaned local files
                orphaned = []
                for local_app in local_apps[:]:  # Copy list to modify during iteration
                    if local_app["app_id"] not in server_app_ids:
                        orphaned.append(local_app["app_id"])
                        # Delete orphaned local config
                        delete_application_config(local_app["app_id"])
                        # Remove from local_apps list
                        local_apps.remove(local_app)
                
                if orphaned:
                    console.print(f"🧹 Cleaned up {len(orphaned)} orphaned local file(s): {', '.join(orphaned)}", style="yellow")
            
        except httpx.HTTPError as e:
            # If server check fails, just show local apps with a warning
            console.print(f"⚠️  Could not sync with server: {e}", style="yellow")
        except Exception as e:
            # Silently continue if sync fails
            pass
    
    if format == "table":
        if not local_apps:
            console.print("No applications registered.", style="yellow")
            return
        
        table = Table(title="Registered Applications")
        table.add_column("App ID", style="cyan")
        table.add_column("Created", style="green")
        table.add_column("Tool Connections", style="magenta")
        table.add_column("Config File", style="white")
        
        for app in local_apps:
            conn_count = len(app.get("tool_connections", {}))
            conn_str = f"{conn_count} connection(s)"
            config_file = f"~/.af/applications/{app['app_id']}.json"
            
            table.add_row(
                app["app_id"],
                app.get("created_at", "N/A")[:10],  # Just date
                conn_str,
                config_file
            )
        
        console.print(table)
        console.print(f"\n📊 Total: {len(local_apps)} application(s)")
    else:
        print_output(
            {"applications": local_apps, "total": len(local_apps)},
            format_type=format,
            title="Registered Applications"
        )


@app.command("show")
def show_application(
    app_id: str = typer.Argument(..., help="Application identifier"),
    reveal_secret: bool = typer.Option(False, "--reveal-secret", help="Reveal the secret key"),
):
    """
    Show details of a registered application.
    
    Example:
        afctl applications show my-slack-bot
        afctl applications show my-slack-bot --reveal-secret
    """
    from af_sdk import load_application_config, ApplicationNotFoundError
    
    try:
        app_config = load_application_config(app_id)
    except ApplicationNotFoundError as e:
        console.print(f"❌ {e}", style="red")
        raise typer.Exit(1)
    
    console.print(f"\n📋 Application: {app_config['app_id']}", style="cyan bold")
    console.print(f"👤 User ID: {app_config.get('user_id', 'N/A')}", style="white")
    console.print(f"🏢 Tenant ID: {app_config.get('tenant_id', 'N/A')}", style="white")
    console.print(f"📅 Created: {app_config.get('created_at', 'N/A')}", style="white")
    console.print(f"🌐 Gateway: {app_config.get('gateway_url', 'N/A')}", style="white")
    
    if reveal_secret:
        console.print(f"\n🔑 Secret Key: {app_config['secret_key']}", style="yellow bold")
        console.print("⚠️  Keep this secret secure!", style="yellow")
    else:
        console.print(f"\n🔑 Secret Key: ••••••••", style="white")
        console.print("   Use --reveal-secret to show", style="dim")
    
    console.print("\n🔌 Tool Connections:", style="cyan bold")
    tool_conns = app_config.get("tool_connections", {})
    if tool_conns:
        for conn_id, scopes in tool_conns.items():
            console.print(f"  • {conn_id}", style="white")
            if scopes:
                console.print(f"    Scopes: {', '.join(scopes)}", style="dim")
    else:
        console.print("  (none)", style="dim")
    
    config_file = Path.home() / ".af" / "applications" / f"{app_id}.json"
    console.print(f"\n💾 Config file: {config_file}", style="green")


@app.command("delete")
def delete_application(
    app_id: str = typer.Argument(..., help="Application identifier"),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation"),
):
    """
    Delete a registered application.
    
    This will:
    - Delete the application registration on the server
    - Remove local credentials
    - Invalidate all active tokens
    
    Example:
        afctl applications delete my-slack-bot
        afctl applications delete my-slack-bot --yes
    """
    config = get_config()
    
    if not config.is_authenticated():
        console.print("❌ Not authenticated. Run 'afctl auth login' first.", style="red")
        raise typer.Exit(1)
    
    # Confirm deletion
    if not yes:
        console.print(f"\n⚠️  This will:", style="yellow bold")
        console.print(f"  • Delete the application registration on the server", style="white")
        console.print(f"  • Remove local credentials from ~/.af/applications/{app_id}.json", style="white")
        console.print(f"  • Invalidate all active tokens for this application", style="white")
        
        confirm = typer.confirm(f"\nAre you sure you want to delete '{app_id}'?", default=False)
        if not confirm:
            console.print("❌ Cancelled", style="yellow")
            raise typer.Exit(0)
    
    # Delete from server
    try:
        response = httpx.delete(
            f"{config.gateway_url}/api/v1/applications/{app_id}",
            headers={"Authorization": f"Bearer {config.access_token}"},
            timeout=30.0
        )
        
        if response.status_code == 404:
            console.print(f"⚠️  Application '{app_id}' not found on server", style="yellow")
        elif response.status_code != 204:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("detail", response.text)
            except:
                pass
            
            console.print(f"❌ Failed to delete from server: {error_detail}", style="red")
            raise typer.Exit(1)
        else:
            console.print(f"✅ Deleted from server", style="green")
        
    except httpx.HTTPError as e:
        console.print(f"❌ Network error: {e}", style="red")
        raise typer.Exit(1)
    
    # Delete local config
    from af_sdk import delete_application_config
    
    deleted = delete_application_config(app_id)
    if deleted:
        console.print(f"✅ Deleted local credentials", style="green")
    else:
        console.print(f"⚠️  Local credentials not found", style="yellow")
    
    console.print(f"\n🎉 Application '{app_id}' deleted successfully", style="green bold")


@app.command("test")
def test_application(
    app_id: str = typer.Argument(..., help="Application identifier"),
):
    """
    Test application authentication.
    
    Attempts to exchange credentials for a token to verify the application
    is properly registered and can authenticate.
    
    Example:
        afctl applications test my-slack-bot
    """
    import asyncio
    from af_sdk import get_application_client, ApplicationNotFoundError, AuthenticationError
    
    async def _test():
        try:
            console.print(f"🔄 Testing authentication for '{app_id}'...", style="cyan")
            
            client = await get_application_client(app_id)
            
            console.print(f"✅ Authentication successful!", style="green bold")
            console.print(f"\n📋 Application: {client._app_id}", style="cyan")
            console.print(f"⏱️  Token expires in: {client._expires_in} seconds", style="white")
            console.print(f"\n🎉 Your application can authenticate and make API calls!", style="green")
            
        except ApplicationNotFoundError as e:
            console.print(f"❌ {e}", style="red")
            raise typer.Exit(1)
        except AuthenticationError as e:
            console.print(f"❌ {e}", style="red")
            raise typer.Exit(1)
    
    asyncio.run(_test())

