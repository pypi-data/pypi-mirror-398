"""Custom exception hierarchy for MCP server."""


class MCPError(Exception):
    """Base exception for all MCP server errors."""

    pass


class ConfigurationError(MCPError):
    """Raised when configuration is invalid or missing."""

    pass


class AuthenticationError(MCPError):
    """Raised when authentication fails."""

    pass


class BPAClientError(MCPError):
    """Raised when BPA API client encounters an error."""

    pass


class PermissionDeniedError(MCPError):
    """Raised when user lacks required permission.

    This is distinct from AuthenticationError which indicates
    the user is not authenticated at all. PermissionDeniedError means
    the user is authenticated but lacks specific permissions.

    Note: Named PermissionDeniedError to avoid shadowing Python's
    built-in PermissionError (an OSError subclass).
    """

    pass
