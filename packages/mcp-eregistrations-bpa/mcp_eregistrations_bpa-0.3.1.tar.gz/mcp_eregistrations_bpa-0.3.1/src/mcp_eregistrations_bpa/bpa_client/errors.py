"""BPA client error handling and translation.

This module provides error classes for BPA API interactions and
translates HTTP errors to AI-friendly ToolError messages.

Error translation follows the pattern:
    "[What happened]: [Why it matters]. [Suggested action]"

Usage:
    from mcp_eregistrations_bpa.bpa_client.errors import translate_error

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise translate_error(e)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp.server.fastmcp.exceptions import ToolError

if TYPE_CHECKING:
    import httpx

__all__ = [
    "BPAClientError",
    "BPAConnectionError",
    "BPATimeoutError",
    "BPAAuthenticationError",
    "BPAPermissionError",
    "BPANotFoundError",
    "BPAValidationError",
    "BPARateLimitError",
    "BPAServerError",
    "translate_error",
    "translate_http_error",
]


class BPAClientError(Exception):
    """Base exception for BPA client errors.

    All BPA client errors inherit from this class.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize BPA client error.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
        """
        super().__init__(message)
        self.status_code = status_code


class BPAConnectionError(BPAClientError):
    """Connection to BPA API failed."""


class BPATimeoutError(BPAClientError):
    """Request to BPA API timed out."""


class BPAAuthenticationError(BPAClientError):
    """Authentication with BPA API failed (401)."""


class BPAPermissionError(BPAClientError):
    """Permission denied by BPA API (403)."""


class BPANotFoundError(BPAClientError):
    """Resource not found in BPA API (404)."""


class BPAValidationError(BPAClientError):
    """Validation error from BPA API (400)."""


class BPARateLimitError(BPAClientError):
    """Rate limit exceeded (429)."""


class BPAServerError(BPAClientError):
    """BPA server error (5xx)."""


def translate_http_error(
    error: httpx.HTTPStatusError,
    *,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
) -> BPAClientError:
    """Translate httpx HTTP error to BPA-specific exception.

    Args:
        error: The httpx HTTP status error.
        resource_type: Optional resource type for context (e.g., "service").
        resource_id: Optional resource ID for context.

    Returns:
        A BPAClientError subclass appropriate for the status code.
    """
    status_code = error.response.status_code
    response_text = error.response.text[:200] if error.response.text else ""

    # Build resource context
    resource_context = ""
    if resource_type:
        resource_context = f" {resource_type}"
        if resource_id is not None:
            resource_context = f" {resource_type} (ID: {resource_id})"

    if status_code == 400:
        msg = f"Invalid request for{resource_context}: {response_text}".strip()
        return BPAValidationError(msg, status_code=status_code)

    if status_code == 401:
        return BPAAuthenticationError(
            "Authentication failed. Token may be invalid or expired.",
            status_code=status_code,
        )

    if status_code == 403:
        return BPAPermissionError(
            f"Access denied to{resource_context}. Check your permissions.",
            status_code=status_code,
        )

    if status_code == 404:
        if resource_type:
            msg = f"{resource_type.capitalize()} not found"
            if resource_id is not None:
                msg = f"{resource_type.capitalize()} with ID {resource_id} not found"
        else:
            msg = "Resource not found"
        return BPANotFoundError(msg, status_code=status_code)

    if status_code == 429:
        return BPARateLimitError(
            "Rate limit exceeded. Please wait before retrying.",
            status_code=status_code,
        )

    if status_code >= 500:
        return BPAServerError(
            f"BPA server error ({status_code}): {response_text}".strip(),
            status_code=status_code,
        )

    # Generic error for other status codes
    return BPAClientError(
        f"BPA API error ({status_code}): {response_text}".strip(),
        status_code=status_code,
    )


def translate_error(
    error: Exception,
    *,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
) -> ToolError:
    """Translate any BPA client error to AI-friendly ToolError.

    This is the main entry point for error translation. It handles
    all exception types and produces consistent AI-friendly messages.

    Error message format:
        "[What happened]: [Why it matters]. [Suggested action]"

    Args:
        error: The exception to translate.
        resource_type: Optional resource type for context.
        resource_id: Optional resource ID for context.

    Returns:
        ToolError with AI-friendly message.
    """
    import httpx

    # First translate httpx errors to BPA-specific errors
    if isinstance(error, httpx.HTTPStatusError):
        error = translate_http_error(
            error, resource_type=resource_type, resource_id=resource_id
        )

    # Now translate to ToolError with AI-friendly message
    if isinstance(error, BPAConnectionError):
        return ToolError(
            "Failed to connect to BPA API: Network or server may be unreachable. "
            "Check your connection and BPA_INSTANCE_URL configuration."
        )

    if isinstance(error, BPATimeoutError):
        return ToolError(
            "BPA API request timed out: The server took too long to respond. "
            "Try again or check if the BPA instance is healthy."
        )

    if isinstance(error, BPAAuthenticationError):
        return ToolError(
            "BPA authentication failed: Your session may have expired. "
            "Run auth_login to re-authenticate."
        )

    if isinstance(error, BPAPermissionError):
        return ToolError(
            f"Permission denied: {error}. "
            "Contact your administrator if you need access."
        )

    if isinstance(error, BPANotFoundError):
        return ToolError(
            f"Resource not found: {error}. "
            "Verify the resource exists and you have access."
        )

    if isinstance(error, BPAValidationError):
        return ToolError(f"Invalid request: {error}. Check your input parameters.")

    if isinstance(error, BPARateLimitError):
        return ToolError(
            "Rate limit exceeded: Too many requests to BPA API. "
            "Wait a moment and try again."
        )

    if isinstance(error, BPAServerError):
        return ToolError(
            f"BPA server error: {error}. "
            "The BPA service may be experiencing issues. Try again later."
        )

    if isinstance(error, BPAClientError):
        return ToolError(f"BPA API error: {error}")

    # Handle httpx connection errors
    if isinstance(error, httpx.ConnectError):
        return ToolError(
            "Failed to connect to BPA API: Network or server may be unreachable. "
            "Check your connection and BPA_INSTANCE_URL configuration."
        )

    if isinstance(error, httpx.TimeoutException):
        return ToolError(
            "BPA API request timed out: The server took too long to respond. "
            "Try again or check if the BPA instance is healthy."
        )

    # Generic fallback
    return ToolError(f"BPA API error: {error}")
