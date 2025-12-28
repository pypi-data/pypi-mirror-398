"""BPA API client module.

This module provides the BPAClient for interacting with the BPA REST API.

Main exports:
    BPAClient: Async HTTP client with retry logic and auth integration.

Example:
    from mcp_eregistrations_bpa.bpa_client import BPAClient

    async with BPAClient() as client:
        services = await client.get("/service")
        service = await client.get("/service/{id}", path_params={"id": 123})
"""

from mcp_eregistrations_bpa.bpa_client.client import (
    BASE_DELAY,
    DEFAULT_TIMEOUT,
    MAX_DELAY,
    MAX_RETRIES,
    NON_RETRYABLE_STATUS_CODES,
    RETRYABLE_STATUS_CODES,
    BPAClient,
)
from mcp_eregistrations_bpa.bpa_client.errors import (
    BPAAuthenticationError,
    BPAClientError,
    BPAConnectionError,
    BPANotFoundError,
    BPAPermissionError,
    BPARateLimitError,
    BPAServerError,
    BPATimeoutError,
    BPAValidationError,
    translate_error,
)
from mcp_eregistrations_bpa.bpa_client.models import (
    Action,
    BPABaseModel,
    Cost,
    Determinant,
    Document,
    Form,
    FormField,
    PaginatedResponse,
    Registration,
    Role,
    Service,
)

__all__ = [
    # Client
    "BPAClient",
    # Client constants
    "MAX_RETRIES",
    "BASE_DELAY",
    "MAX_DELAY",
    "DEFAULT_TIMEOUT",
    "RETRYABLE_STATUS_CODES",
    "NON_RETRYABLE_STATUS_CODES",
    # Errors
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
    # Models
    "BPABaseModel",
    "Service",
    "Registration",
    "FormField",
    "Determinant",
    "Role",
    "Cost",
    "Document",
    "Action",
    "Form",
    "PaginatedResponse",
]
