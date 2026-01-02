"""Permission enforcement for MCP tools.

This module provides guards and utility functions to enforce
BPA permissions before tool execution. All permission checks
are server-side and based on JWT token claims.

Usage in MCP tools:
    @mcp.tool()
    async def service_create(name: str) -> dict[str, object]:
        # Ensure write permission before proceeding
        access_token = await ensure_write_permission()
        # ... use access_token for BPA API call
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.server.fastmcp.exceptions import ToolError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from mcp_eregistrations_bpa.auth.token_manager import TokenManager

__all__ = [
    "PERMISSION_VIEWER",
    "PERMISSION_SERVICE_DESIGNER",
    "WRITE_PERMISSIONS",
    "ensure_authenticated",
    "ensure_write_permission",
    "check_permission",
]

# Permission constants
PERMISSION_VIEWER = "viewer"
PERMISSION_SERVICE_DESIGNER = "service_designer"

# Roles that allow write operations
WRITE_PERMISSIONS: list[str] = [PERMISSION_SERVICE_DESIGNER]


def get_token_manager() -> TokenManager:
    """Get the global token manager instance.

    Uses late import to avoid circular dependency with server.py.

    Returns:
        The global TokenManager instance.
    """
    from mcp_eregistrations_bpa.server import get_token_manager as _get_tm

    return _get_tm()


async def ensure_authenticated() -> str:
    """Ensure user is authenticated and return access token.

    Automatically triggers browser-based login if not authenticated.
    Checks authentication status and token expiry. Calls
    token_manager.get_access_token() which handles automatic
    refresh if the token is near expiry.

    Returns:
        Valid access token for BPA API calls.

    Raises:
        ToolError: If authentication fails or token expired and cannot refresh.
    """
    token_manager = get_token_manager()
    logger.debug("Checking authentication status...")

    # Auto-trigger login if not authenticated
    if not token_manager.is_authenticated():
        logger.info("Not authenticated - initiating browser login flow")
        from mcp_eregistrations_bpa.auth.oidc import perform_browser_login
        from mcp_eregistrations_bpa.exceptions import AuthenticationError

        try:
            result = await perform_browser_login()
            if result.get("error"):
                logger.error("Authentication failed: %s", result.get("message"))
                raise ToolError(str(result.get("message", "Authentication failed")))
            logger.info("Authentication successful for user: %s", result.get("user"))
        except AuthenticationError as e:
            logger.error("Authentication error: %s", e)
            raise ToolError(str(e))

    # Check for expired token (shouldn't happen right after login, but handle it)
    if token_manager.is_token_expired():
        logger.warning("Token expired - user needs to re-authenticate")
        raise ToolError("Session expired. Please run auth_login again.")

    logger.debug("User authenticated: %s", token_manager.user_email)
    # This will auto-refresh if within 5 minutes of expiry
    return await token_manager.get_access_token()


async def ensure_write_permission() -> str:
    """Ensure user has write permission and return access token.

    Combines authentication check with write permission verification.
    Checks if user has any role in WRITE_PERMISSIONS.

    Returns:
        Valid access token for BPA API calls.

    Raises:
        ToolError: If not authenticated or lacks write permission.
    """
    # First ensure authenticated (raises if not)
    token = await ensure_authenticated()

    # Check for write permission
    token_manager = get_token_manager()
    user_permissions = set(token_manager.permissions)

    if not user_permissions.intersection(WRITE_PERMISSIONS):
        raise ToolError(
            "Permission denied: You don't have write access. "
            "Contact your administrator."
        )

    return token


def check_permission(required_permission: str) -> None:
    """Check if user has a specific permission.

    This is a synchronous check that also validates authentication status.
    Raises ToolError if not authenticated or if permission is missing.

    Args:
        required_permission: The permission role required.

    Raises:
        ToolError: If not authenticated or user lacks the required permission.
    """
    token_manager = get_token_manager()

    # Verify authentication first (sync check - doesn't refresh)
    if not token_manager.is_authenticated():
        raise ToolError("Not authenticated. Run auth_login first.")

    if token_manager.is_token_expired():
        raise ToolError("Session expired. Please run auth_login again.")

    if required_permission not in token_manager.permissions:
        raise ToolError(
            f"Permission denied: You need '{required_permission}' permission. "
            "Contact your administrator."
        )
