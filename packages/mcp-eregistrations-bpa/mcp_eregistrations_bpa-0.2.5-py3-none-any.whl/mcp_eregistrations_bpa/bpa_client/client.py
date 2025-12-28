"""BPA API async HTTP client with retry logic.

This module provides the main BPAClient class for interacting with the
BPA REST API. It features:

- Async HTTP operations using httpx
- Exponential backoff retry for transient errors (429, 502, 503, 504)
- No retry for client errors (400, 401, 403, 404)
- Token-based authorization via auth module
- AI-friendly error translation

Usage:
    from mcp_eregistrations_bpa.bpa_client import BPAClient

    async with BPAClient() as client:
        services = await client.get("/service")
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, cast

import httpx

from mcp_eregistrations_bpa.bpa_client.errors import (
    BPAClientError,
    BPAConnectionError,
    BPATimeoutError,
    translate_http_error,
)
from mcp_eregistrations_bpa.config import load_config

if TYPE_CHECKING:
    from types import TracebackType

__all__ = [
    "BPAClient",
    "MAX_RETRIES",
    "BASE_DELAY",
    "MAX_DELAY",
    "DEFAULT_TIMEOUT",
    "RETRYABLE_STATUS_CODES",
    "NON_RETRYABLE_STATUS_CODES",
]

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 10.0  # seconds

# Timeout configuration (NFR15: 5 second default)
DEFAULT_TIMEOUT = 5.0  # seconds

# Status codes that should trigger retry
RETRYABLE_STATUS_CODES = frozenset({429, 502, 503, 504})

# Status codes that should NOT be retried (client errors)
NON_RETRYABLE_STATUS_CODES = frozenset({400, 401, 403, 404})


def calculate_backoff_delay(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter.

    Uses exponential backoff: delay = min(BASE_DELAY * 2^attempt, MAX_DELAY)
    Adds small jitter to prevent thundering herd.

    Args:
        attempt: The retry attempt number (0-indexed).

    Returns:
        The delay in seconds before next retry.
    """
    import random

    delay = min(BASE_DELAY * (2**attempt), MAX_DELAY)
    # Add up to 10% jitter
    jitter = delay * 0.1 * random.random()
    return float(delay + jitter)


class BPAClient:
    """Async HTTP client for BPA API with retry logic.

    Features:
    - Token-based authorization header injection
    - Exponential backoff retry for transient errors
    - AI-friendly error translation
    - Async context manager support

    Attributes:
        base_url: The BPA instance base URL.
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts for transient errors.

    Example:
        async with BPAClient() as client:
            # GET request
            services = await client.get("/service")

            # GET with path parameters
            service = await client.get("/service/{id}", path_params={"id": 123})

            # POST with body
            result = await client.post("/service", json={"name": "New Service"})
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        """Initialize BPA client.

        Args:
            base_url: BPA instance base URL. If None, uses config.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts for transient errors.
        """
        if base_url is None:
            config = load_config()
            base_url = str(config.bpa_instance_url)

        # Ensure base URL ends with API path (v2016.06, not /v3)
        if not base_url.endswith("/bparest/bpa/v2016/06"):
            base_url = base_url.rstrip("/") + "/bparest/bpa/v2016/06"

        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> BPAClient:
        """Enter async context manager."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get the HTTP client, ensuring it's initialized.

        Returns:
            The httpx async client.

        Raises:
            RuntimeError: If client is not initialized (use async with).
        """
        if self._client is None:
            msg = "BPAClient must be used as an async context manager"
            raise RuntimeError(msg)
        return self._client

    async def _get_auth_header(self) -> dict[str, str]:
        """Get authorization header with current access token.

        Returns:
            Headers dict with Authorization header.

        Raises:
            ToolError: If not authenticated or token expired.
        """
        from mcp_eregistrations_bpa.auth.permissions import ensure_authenticated

        token = await ensure_authenticated()
        return {"Authorization": f"Bearer {token}"}

    def _format_url(self, endpoint: str, path_params: dict[str, Any] | None) -> str:
        """Format URL endpoint with path parameters.

        Args:
            endpoint: URL endpoint template (e.g., "/service/{id}").
            path_params: Dictionary of path parameters.

        Returns:
            Formatted URL path.
        """
        if path_params:
            return endpoint.format(**path_params)
        return endpoint

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        *,
        path_params: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        resource_type: str | None = None,
        resource_id: str | int | None = None,
    ) -> httpx.Response:
        """Execute HTTP request with retry logic.

        Retries on transient errors (429, 502, 503, 504) with exponential backoff.
        Does NOT retry on client errors (400, 401, 403, 404).

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: URL endpoint template.
            path_params: Path parameters for URL formatting.
            params: Query parameters.
            json: JSON body for POST/PUT.
            resource_type: Resource type for error context.
            resource_id: Resource ID for error context.

        Returns:
            httpx Response object.

        Raises:
            BPAClientError: On non-retryable errors or after max retries.
        """
        client = self._get_client()
        url = self._format_url(endpoint, path_params)
        headers = await self._get_auth_header()

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                # Log request details (DEBUG level for verbose output)
                logger.debug(
                    "BPA API Request: %s %s%s",
                    method,
                    self.base_url,
                    url,
                )
                if params:
                    logger.debug("  Query params: %s", params)
                if json:
                    logger.debug("  Request body: %s", json)

                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json,
                )

                # Log response (INFO for success, DEBUG for body)
                logger.info(
                    "BPA API Response: %s %s → %d %s",
                    method,
                    url,
                    response.status_code,
                    response.reason_phrase,
                )

                # Check for HTTP errors
                if response.status_code >= 400:
                    # Don't retry client errors
                    if response.status_code in NON_RETRYABLE_STATUS_CODES:
                        error = httpx.HTTPStatusError(
                            f"HTTP {response.status_code}",
                            request=response.request,
                            response=response,
                        )
                        raise translate_http_error(
                            error,
                            resource_type=resource_type,
                            resource_id=resource_id,
                        )

                    # Check if retryable
                    if response.status_code in RETRYABLE_STATUS_CODES:
                        if attempt < self.max_retries:
                            delay = calculate_backoff_delay(attempt)
                            logger.warning(
                                "Retryable error %d on %s %s (attempt %d/%d), "
                                "retrying in %.2fs",
                                response.status_code,
                                method,
                                url,
                                attempt + 1,
                                self.max_retries + 1,
                                delay,
                            )
                            await asyncio.sleep(delay)
                            continue

                    # Non-retryable or out of retries
                    error = httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    raise translate_http_error(
                        error,
                        resource_type=resource_type,
                        resource_id=resource_id,
                    )

                return response

            except httpx.ConnectError as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = calculate_backoff_delay(attempt)
                    logger.warning(
                        "Connection error on %s %s (attempt %d/%d), "
                        "retrying in %.2fs: %s",
                        method,
                        url,
                        attempt + 1,
                        self.max_retries + 1,
                        delay,
                        e,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise BPAConnectionError(
                    f"Failed to connect to BPA API after {self.max_retries + 1} "
                    f"attempts: {e}"
                ) from e

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = calculate_backoff_delay(attempt)
                    logger.warning(
                        "Timeout on %s %s (attempt %d/%d), retrying in %.2fs",
                        method,
                        url,
                        attempt + 1,
                        self.max_retries + 1,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise BPATimeoutError(
                    f"BPA API request timed out after {self.max_retries + 1} attempts"
                ) from e

            except BPAClientError:
                # Re-raise BPA errors without wrapping
                raise

        # Should not reach here, but just in case
        if last_error:
            raise BPAClientError(f"Request failed: {last_error}")
        raise BPAClientError("Request failed for unknown reason")

    async def get(
        self,
        endpoint: str,
        *,
        path_params: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        resource_type: str | None = None,
        resource_id: str | int | None = None,
    ) -> dict[str, Any]:
        """Execute GET request.

        Args:
            endpoint: URL endpoint template.
            path_params: Path parameters for URL formatting.
            params: Query parameters.
            resource_type: Resource type for error context.
            resource_id: Resource ID for error context.

        Returns:
            JSON response as dictionary.

        Raises:
            BPAClientError: On API errors.
        """
        response = await self._request_with_retry(
            "GET",
            endpoint,
            path_params=path_params,
            params=params,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        return cast(dict[str, Any], response.json())

    async def get_list(
        self,
        endpoint: str,
        *,
        path_params: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        resource_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute GET request expecting a list response.

        Args:
            endpoint: URL endpoint template.
            path_params: Path parameters for URL formatting.
            params: Query parameters.
            resource_type: Resource type for error context.

        Returns:
            JSON response as list of dictionaries.

        Raises:
            BPAClientError: On API errors.
        """
        response = await self._request_with_retry(
            "GET",
            endpoint,
            path_params=path_params,
            params=params,
            resource_type=resource_type,
        )
        result = response.json()
        if isinstance(result, list):
            return cast(list[dict[str, Any]], result)
        # Some APIs wrap lists in an object
        if isinstance(result, dict) and "items" in result:
            return cast(list[dict[str, Any]], result["items"])
        return [cast(dict[str, Any], result)] if result else []

    async def post(
        self,
        endpoint: str,
        *,
        path_params: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        resource_type: str | None = None,
    ) -> dict[str, Any]:
        """Execute POST request.

        Args:
            endpoint: URL endpoint template.
            path_params: Path parameters for URL formatting.
            params: Query parameters.
            json: JSON body.
            resource_type: Resource type for error context.

        Returns:
            JSON response as dictionary.

        Raises:
            BPAClientError: On API errors.
        """
        response = await self._request_with_retry(
            "POST",
            endpoint,
            path_params=path_params,
            params=params,
            json=json,
            resource_type=resource_type,
        )
        return cast(dict[str, Any], response.json())

    async def put(
        self,
        endpoint: str,
        *,
        path_params: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        resource_type: str | None = None,
        resource_id: str | int | None = None,
    ) -> dict[str, Any]:
        """Execute PUT request.

        Args:
            endpoint: URL endpoint template.
            path_params: Path parameters for URL formatting.
            params: Query parameters.
            json: JSON body.
            resource_type: Resource type for error context.
            resource_id: Resource ID for error context.

        Returns:
            JSON response as dictionary.

        Raises:
            BPAClientError: On API errors.
        """
        response = await self._request_with_retry(
            "PUT",
            endpoint,
            path_params=path_params,
            params=params,
            json=json,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        return cast(dict[str, Any], response.json())

    async def delete(
        self,
        endpoint: str,
        *,
        path_params: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        resource_type: str | None = None,
        resource_id: str | int | None = None,
    ) -> dict[str, Any] | None:
        """Execute DELETE request.

        Args:
            endpoint: URL endpoint template.
            path_params: Path parameters for URL formatting.
            params: Query parameters.
            resource_type: Resource type for error context.
            resource_id: Resource ID for error context.

        Returns:
            JSON response as dictionary, or None if no content.

        Raises:
            BPAClientError: On API errors.
        """
        response = await self._request_with_retry(
            "DELETE",
            endpoint,
            path_params=path_params,
            params=params,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        if response.status_code == 204:
            return None
        return cast(dict[str, Any], response.json())
