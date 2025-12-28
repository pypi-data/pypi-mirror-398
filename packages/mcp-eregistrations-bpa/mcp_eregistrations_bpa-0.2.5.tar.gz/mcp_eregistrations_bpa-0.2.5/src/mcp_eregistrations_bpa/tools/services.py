"""MCP tools for BPA service operations.

This module provides tools for listing, retrieving, creating, and updating BPA services.

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED

API Endpoints used:
- GET /service - List all services
- GET /service/{id} - Get service by ID
- POST /service - Create new service
- PUT /service - Update service
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.audit.context import (
    NotAuthenticatedError,
    get_current_user_email,
)
from mcp_eregistrations_bpa.audit.logger import AuditLogger
from mcp_eregistrations_bpa.bpa_client import BPAClient
from mcp_eregistrations_bpa.bpa_client.errors import (
    BPAClientError,
    BPANotFoundError,
    translate_error,
)

__all__ = [
    "service_list",
    "service_get",
    "service_create",
    "service_update",
    "register_service_tools",
]


async def service_list() -> dict[str, Any]:
    """List all BPA services.

    Returns all services the authenticated user has access to.
    Each service includes id, name, status, and registration_count.

    Returns:
        dict: List of services with total count.
            - services: List of service objects
            - total: Total number of services
    """
    try:
        async with BPAClient() as client:
            services_data = await client.get_list("/service", resource_type="service")
    except BPAClientError as e:
        raise translate_error(e, resource_type="service")

    # Transform to consistent output format with registration_count
    services = []
    for svc in services_data:
        services.append(
            {
                "id": svc.get("id"),
                "name": svc.get("name"),
                "status": svc.get("status"),
                "registration_count": svc.get("registrationCount", 0),
            }
        )

    return {
        "services": services,
        "total": len(services),
    }


async def service_get(service_id: str | int) -> dict[str, Any]:
    """Get details of a BPA service by ID.

    Returns complete service details including registrations summary.

    Args:
        service_id: The unique identifier of the service.

    Returns:
        dict: Complete service details including:
            - id, name, description, status, short_name
            - registrations: List of registration summaries
            - created_at, updated_at timestamps
    """
    try:
        async with BPAClient() as client:
            try:
                service_data = await client.get(
                    "/service/{id}",
                    path_params={"id": service_id},
                    resource_type="service",
                    resource_id=service_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )

            # Get registrations for this service
            registrations_data = await client.get_list(
                "/registration",
                params={"serviceId": service_id},
                resource_type="registration",
            )
    except ToolError:
        # Re-raise ToolError (from BPANotFoundError handling above)
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)

    # Transform registrations to summary format
    registrations = [
        {"id": reg.get("id"), "name": reg.get("name")} for reg in registrations_data
    ]

    return {
        "id": service_data.get("id"),
        "name": service_data.get("name"),
        "description": service_data.get("description"),
        "status": service_data.get("status"),
        "short_name": service_data.get("shortName"),
        "registrations": registrations,
        "created_at": service_data.get("createdAt"),
        "updated_at": service_data.get("updatedAt"),
    }


def _validate_service_create_params(
    name: str,
    description: str | None,
    short_name: str | None,
) -> dict[str, str]:
    """Validate service_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        name: Service name (required).
        description: Service description (optional).
        short_name: Short name for the service (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not name or not name.strip():
        errors.append("'name' is required and cannot be empty")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if short_name and len(short_name.strip()) > 50:
        errors.append("'short_name' must be 50 characters or less")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot create service: {error_msg}. Check required fields.")

    params: dict[str, str] = {"name": name.strip()}
    if description:
        params["description"] = description.strip()
    if short_name:
        params["shortName"] = short_name.strip()

    return params


async def service_create(
    name: str,
    description: str | None = None,
    short_name: str | None = None,
) -> dict[str, Any]:
    """Create a new BPA service.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Create PENDING audit record
    3. Execute POST /service API call
    4. Update audit record to SUCCESS or FAILED

    Args:
        name: Name of the service (required).
        description: Description of the service (optional).
        short_name: Short name for the service (optional).

    Returns:
        dict: Created service details including:
            - id: The new service ID
            - name, description, status, short_name
            - created_at timestamp

    Raises:
        ToolError: If validation fails, not authenticated, or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_service_create_params(name, description, short_name)

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Create audit record BEFORE API call (audit-before-write pattern)
    audit_logger = AuditLogger()
    audit_id = await audit_logger.record_pending(
        user_email=user_email,
        operation_type="create",
        object_type="service",
        params=validated_params,
    )

    try:
        async with BPAClient() as client:
            service_data = await client.post(
                "/service",
                json=validated_params,
                resource_type="service",
            )

        # Mark audit as success
        await audit_logger.mark_success(
            audit_id,
            result={
                "service_id": service_data.get("id"),
                "name": service_data.get("name"),
            },
        )

        return {
            "id": service_data.get("id"),
            "name": service_data.get("name"),
            "description": service_data.get("description"),
            "status": service_data.get("status"),
            "short_name": service_data.get("shortName"),
            "created_at": service_data.get("createdAt"),
            "audit_id": audit_id,
        }

    except BPAClientError as e:
        # Mark audit as failed
        await audit_logger.mark_failed(audit_id, str(e))
        raise translate_error(e, resource_type="service")


def _validate_service_update_params(
    service_id: str | int,
    name: str | None,
    description: str | None,
    short_name: str | None,
) -> dict[str, Any]:
    """Validate service_update parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.

    Args:
        service_id: ID of service to update (required).
        name: New name (optional).
        description: New description (optional).
        short_name: New short name (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not service_id:
        errors.append("'service_id' is required")

    if name is not None and not name.strip():
        errors.append("'name' cannot be empty when provided")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if short_name and len(short_name.strip()) > 50:
        errors.append("'short_name' must be 50 characters or less")

    # At least one field must be provided for update
    if name is None and description is None and short_name is None:
        errors.append(
            "At least one field (name, description, short_name) must be provided"
        )

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot update service: {error_msg}. Check required fields.")

    params: dict[str, Any] = {"id": service_id}
    if name is not None:
        params["name"] = name.strip()
    if description is not None:
        params["description"] = description.strip()
    if short_name is not None:
        params["shortName"] = short_name.strip()

    return params


async def service_update(
    service_id: str | int,
    name: str | None = None,
    description: str | None = None,
    short_name: str | None = None,
) -> dict[str, Any]:
    """Update an existing BPA service.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Capture current state for rollback
    3. Create PENDING audit record
    4. Execute PUT /service API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        service_id: ID of the service to update (required).
        name: New name for the service (optional).
        description: New description for the service (optional).
        short_name: New short name for the service (optional).

    Returns:
        dict: Updated service details including:
            - id, name, description, status, short_name
            - updated_at timestamp
            - previous_state: The state before update (for rollback reference)
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, service not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_service_update_params(
        service_id, name, description, short_name
    )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Capture current state for rollback BEFORE making changes
    try:
        async with BPAClient() as client:
            try:
                previous_state = await client.get(
                    "/service/{id}",
                    path_params={"id": service_id},
                    resource_type="service",
                    resource_id=service_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)

    # Create audit record BEFORE API call (audit-before-write pattern)
    audit_logger = AuditLogger()
    audit_id = await audit_logger.record_pending(
        user_email=user_email,
        operation_type="update",
        object_type="service",
        object_id=str(service_id),
        params={
            "changes": validated_params,
            "previous_state": {
                "name": previous_state.get("name"),
                "description": previous_state.get("description"),
                "shortName": previous_state.get("shortName"),
            },
        },
    )

    try:
        async with BPAClient() as client:
            service_data = await client.put(
                "/service",
                json=validated_params,
                resource_type="service",
                resource_id=service_id,
            )

        # Mark audit as success
        await audit_logger.mark_success(
            audit_id,
            result={
                "service_id": service_data.get("id"),
                "name": service_data.get("name"),
                "changes_applied": {
                    k: v for k, v in validated_params.items() if k != "id"
                },
            },
        )

        return {
            "id": service_data.get("id"),
            "name": service_data.get("name"),
            "description": service_data.get("description"),
            "status": service_data.get("status"),
            "short_name": service_data.get("shortName"),
            "updated_at": service_data.get("updatedAt"),
            "previous_state": {
                "name": previous_state.get("name"),
                "description": previous_state.get("description"),
                "short_name": previous_state.get("shortName"),
            },
            "audit_id": audit_id,
        }

    except BPAClientError as e:
        # Mark audit as failed
        await audit_logger.mark_failed(audit_id, str(e))
        raise translate_error(e, resource_type="service", resource_id=service_id)


def register_service_tools(mcp: Any) -> None:
    """Register service tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Read operations
    mcp.tool()(service_list)
    mcp.tool()(service_get)
    # Write operations (audit-before-write pattern)
    mcp.tool()(service_create)
    mcp.tool()(service_update)
