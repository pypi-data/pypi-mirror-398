"""MCP server for eRegistrations BPA platform."""

import webbrowser

from fastmcp import FastMCP

from mcp_eregistrations_bpa.auth import (
    CallbackServer,
    TokenManager,
    build_authorization_url,
    discover_oidc_config,
    exchange_code_for_tokens,
    generate_pkce_pair,
    generate_state,
)
from mcp_eregistrations_bpa.config import load_config
from mcp_eregistrations_bpa.exceptions import AuthenticationError
from mcp_eregistrations_bpa.tools import (
    register_action_tools,
    register_analysis_tools,
    register_audit_tools,
    register_bot_tools,
    register_cost_tools,
    register_determinant_tools,
    register_document_requirement_tools,
    register_field_tools,
    register_registration_tools,
    register_role_tools,
    register_rollback_tools,
    register_service_tools,
)

mcp = FastMCP("eregistrations-bpa")

# Register BPA tools
register_service_tools(mcp)
register_registration_tools(mcp)
register_field_tools(mcp)
register_determinant_tools(mcp)
register_action_tools(mcp)
register_bot_tools(mcp)
register_role_tools(mcp)
register_document_requirement_tools(mcp)
register_cost_tools(mcp)
register_analysis_tools(mcp)
register_audit_tools(mcp)
register_rollback_tools(mcp)

# Global token manager instance (in-memory storage)
_token_manager = TokenManager()


@mcp.tool()
async def auth_login() -> dict[str, object]:
    """Authenticate with BPA via browser-based Keycloak login.

    This tool initiates the OIDC authentication flow:
    1. Discovers Keycloak endpoints from BPA instance
    2. Opens browser to Keycloak login page
    3. Waits for callback with authorization code
    4. Exchanges code for tokens
    5. Returns success with user info

    Returns:
        dict: Authentication result with user email and session duration.
    """
    # Load configuration
    config = load_config()

    # Discover OIDC endpoints (uses keycloak_url/realm if configured, else BPA URL)
    oidc_config = await discover_oidc_config(config.oidc_discovery_url)

    # Generate PKCE pair and state
    code_verifier, code_challenge = generate_pkce_pair()
    state = generate_state()

    # Start callback server
    callback_server = CallbackServer()
    callback_server.start()

    try:
        # Build authorization URL
        auth_url = build_authorization_url(
            authorization_endpoint=oidc_config.authorization_endpoint,
            client_id=config.keycloak_client_id,
            redirect_uri=callback_server.redirect_uri,
            code_challenge=code_challenge,
            state=state,
        )

        # Open browser
        if not webbrowser.open(auth_url):
            return {
                "error": True,
                "message": (
                    "Cannot open browser for authentication. "
                    f"Please open this URL manually: {auth_url}"
                ),
            }

        # Wait for callback
        code = await callback_server.wait_for_callback(expected_state=state)

        # Exchange code for tokens
        token_response = await exchange_code_for_tokens(
            token_endpoint=oidc_config.token_endpoint,
            code=code,
            code_verifier=code_verifier,
            redirect_uri=callback_server.redirect_uri,
            client_id=config.keycloak_client_id,
        )

        # Store tokens
        _token_manager.store_tokens(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            expires_in=token_response.expires_in,
            token_endpoint=oidc_config.token_endpoint,
            client_id=config.keycloak_client_id,
        )

        return {
            "success": True,
            "message": (
                f"Authenticated as {_token_manager.user_email}. "
                f"Session valid for {_token_manager.expires_in_minutes} minutes."
            ),
            "user_email": _token_manager.user_email,
            "session_expires_in_minutes": _token_manager.expires_in_minutes,
        }

    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(
            f"Authentication failed: {e}. Please try again."
        ) from e
    finally:
        callback_server.stop()


async def get_connection_status() -> dict[str, object]:
    """Get current BPA connection status (internal implementation).

    Returns connection state, authenticated user, permissions, and session info.
    This is a read-only operation that does not trigger token refresh.

    Returns:
        dict: Connection status with instance URL, user, permissions, and expiry.
    """
    config = load_config()

    # Check if not authenticated
    if not _token_manager.is_authenticated():
        return {
            "connected": False,
            "instance_url": config.bpa_instance_url,
            "message": "Not authenticated. Run auth_login to connect.",
        }

    # Check if token has already expired
    if _token_manager.is_token_expired():
        return {
            "connected": False,
            "instance_url": config.bpa_instance_url,
            "message": "Session expired. Run auth_login to reconnect.",
        }

    # Return full authenticated status
    return {
        "connected": True,
        "instance_url": config.bpa_instance_url,
        "user": _token_manager.user_email,
        "permissions": _token_manager.permissions,
        "session_expires_in": f"{_token_manager.expires_in_minutes} minutes",
    }


@mcp.tool()
async def connection_status() -> dict[str, object]:
    """View current BPA connection status.

    Returns connection state, authenticated user, permissions, and session info.
    This is a read-only operation that does not trigger token refresh.

    Returns:
        dict: Connection status with instance URL, user, permissions, and expiry.
    """
    return await get_connection_status()


def get_token_manager() -> TokenManager:
    """Get the global token manager instance.

    This is used by other modules to access the authenticated session.

    Returns:
        The global TokenManager instance.
    """
    return _token_manager
