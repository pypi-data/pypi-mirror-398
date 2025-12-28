"""User context extraction for audit logging.

This module provides helpers to get the current authenticated user's
context for audit logging purposes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_eregistrations_bpa.auth.token_manager import TokenManager


def get_token_manager() -> TokenManager:
    """Get the global token manager instance.

    Uses late import to avoid circular dependency.

    Returns:
        The global TokenManager instance.
    """
    from mcp_eregistrations_bpa.server import get_token_manager as _get_tm

    return _get_tm()


class NotAuthenticatedError(Exception):
    """Raised when user is not authenticated for audit operations."""

    pass


def get_current_user_email() -> str:
    """Get the current authenticated user's email for audit logging.

    This function should be called before any write operation to capture
    the user context for the audit log.

    Returns:
        The authenticated user's email address.

    Raises:
        NotAuthenticatedError: If no user is authenticated or email unavailable.
    """
    token_manager = get_token_manager()

    if not token_manager.is_authenticated():
        raise NotAuthenticatedError(
            "Cannot perform write operation: User not authenticated. "
            "Run auth_login first."
        )

    if token_manager.is_token_expired():
        raise NotAuthenticatedError(
            "Cannot perform write operation: Session expired. Run auth_login again."
        )

    email = token_manager.user_email
    if not email:  # Catches None, empty string, and whitespace-only
        raise NotAuthenticatedError(
            "Cannot perform write operation: User email not available. "
            "Please re-authenticate."
        )

    return email
