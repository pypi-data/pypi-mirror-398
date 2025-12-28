"""MCP tools for BPA role operations.

This module provides tools for listing, retrieving, creating, updating,
and deleting BPA roles. Roles are access control entities that define
user permissions within a service.

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED

API Endpoints used:
- GET /service/{service_id}/role - List roles for a service
- GET /role/{role_id} - Get role by ID
- POST /service/{service_id}/role - Create role within service
- PUT /role - Update role
- DELETE /role/{role_id} - Delete role
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
    "role_list",
    "role_get",
    "role_create",
    "role_update",
    "role_delete",
    "register_role_tools",
]


def _transform_role_response(data: dict[str, Any]) -> dict[str, Any]:
    """Transform role API response from camelCase to snake_case.

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "assigned_to": data.get("assignedTo"),
        "description": data.get("description"),
        "service_id": data.get("serviceId"),
    }


async def role_list(service_id: str | int) -> dict[str, Any]:
    """List all roles for a BPA service.

    Returns roles configured for the specified service.
    Each role includes id, name, and description.

    Args:
        service_id: The service ID to list roles for (required).

    Returns:
        dict: List of roles with total count.
            - roles: List of role objects
            - service_id: The queried service ID
            - total: Total number of roles
    """
    if not service_id:
        raise ToolError(
            "Cannot list roles: 'service_id' is required. "
            "Use 'service_list' to find valid service IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                roles_data = await client.get_list(
                    "/service/{service_id}/role",
                    path_params={"service_id": service_id},
                    resource_type="role",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role")

    # Transform to consistent output format
    roles = [_transform_role_response(role) for role in roles_data]

    return {
        "roles": roles,
        "service_id": service_id,
        "total": len(roles),
    }


async def role_get(role_id: str | int) -> dict[str, Any]:
    """Get details of a BPA role by ID.

    Returns complete role details.

    Args:
        role_id: The unique identifier of the role.

    Returns:
        dict: Complete role details including:
            - id, name, description
            - service_id: The parent service ID
    """
    if not role_id:
        raise ToolError(
            "Cannot get role: 'role_id' is required. "
            "Use 'role_list' with service_id to find valid role IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                role_data = await client.get(
                    "/role/{role_id}",
                    path_params={"role_id": role_id},
                    resource_type="role",
                    resource_id=role_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Role '{role_id}' not found. "
                    "Use 'role_list' with service_id to see available roles."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role", resource_id=role_id)

    return _transform_role_response(role_data)


def _validate_role_create_params(
    service_id: str | int,
    name: str,
    assigned_to: int,
    description: str | None,
) -> dict[str, Any]:
    """Validate role_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Role name (required).
        assigned_to: User or group ID to assign the role to (required).
        description: Role description (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not service_id:
        errors.append("'service_id' is required")

    if not name or not name.strip():
        errors.append("'name' is required and cannot be empty")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if assigned_to is None:
        errors.append("'assigned_to' is required")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot create role: {error_msg}. Check required fields.")

    params: dict[str, Any] = {
        "name": name.strip(),
        "assignedTo": int(assigned_to),
    }
    if description:
        params["description"] = description.strip()

    return params


async def role_create(
    service_id: str | int,
    name: str,
    assigned_to: int,
    description: str | None = None,
) -> dict[str, Any]:
    """Create a new BPA role within a service.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Verify parent service exists (no audit if service not found)
    3. Create PENDING audit record
    4. Execute POST /service/{service_id}/role API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        service_id: ID of the parent service (required).
        name: Name of the role (required).
        assigned_to: User or group ID to assign the role to (required).
        description: Description of the role (optional).

    Returns:
        dict: Created role details including:
            - id: The new role ID
            - name, description, assigned_to
            - service_id: The parent service ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, service not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_role_create_params(
        service_id, name, assigned_to, description
    )

    # Get authenticated user for audit (before any API calls)
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Verify parent service exists before creating audit record
            try:
                await client.get(
                    "/service/{id}",
                    path_params={"id": service_id},
                    resource_type="service",
                    resource_id=service_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Cannot create role: Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="role",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                role_data = await client.post(
                    "/service/{service_id}/role",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="role",
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "role_id": role_data.get("id"),
                        "name": role_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                result = _transform_role_response(role_data)
                result["service_id"] = service_id  # Ensure service_id is always set
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="role")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


def _validate_role_update_params(
    role_id: str | int,
    name: str | None,
    assigned_to: int | None,
    description: str | None,
) -> dict[str, Any]:
    """Validate role_update parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.

    Args:
        role_id: ID of role to update (required).
        name: New name (optional).
        assigned_to: New user or group ID to assign the role to (optional).
        description: New description (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not role_id:
        errors.append("'role_id' is required")

    if name is not None and not name.strip():
        errors.append("'name' cannot be empty when provided")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    # At least one field must be provided for update
    if name is None and assigned_to is None and description is None:
        errors.append(
            "At least one field (name, assigned_to, description) must be provided"
        )

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot update role: {error_msg}. Check required fields.")

    params: dict[str, Any] = {"id": role_id}
    if name is not None:
        params["name"] = name.strip()
    if assigned_to is not None:
        params["assignedTo"] = int(assigned_to)
    if description is not None:
        params["description"] = description.strip()

    return params


async def role_update(
    role_id: str | int,
    name: str | None = None,
    assigned_to: int | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Update an existing BPA role.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Capture current state for rollback
    3. Create PENDING audit record
    4. Execute PUT /role API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        role_id: ID of the role to update (required).
        name: New name for the role (optional).
        assigned_to: New user or group ID to assign the role to (optional).
        description: New description for the role (optional).

    Returns:
        dict: Updated role details including:
            - id, name, description, assigned_to
            - service_id: The parent service ID
            - previous_state: The state before update (for rollback reference)
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, role not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_role_update_params(
        role_id, name, assigned_to, description
    )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Capture current state for rollback BEFORE making changes
            try:
                previous_state = await client.get(
                    "/role/{role_id}",
                    path_params={"role_id": role_id},
                    resource_type="role",
                    resource_id=role_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Role '{role_id}' not found. "
                    "Use 'role_list' with service_id to see available roles."
                )

            # Merge provided changes with current state for full object PUT
            full_params = {
                "id": role_id,
                "name": validated_params.get("name", previous_state.get("name")),
                "assignedTo": validated_params.get(
                    "assignedTo", previous_state.get("assignedTo")
                ),
                "description": validated_params.get(
                    "description", previous_state.get("description")
                ),
                "serviceId": previous_state.get("serviceId"),
            }

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="role",
                object_id=str(role_id),
                params={
                    "changes": validated_params,
                },
            )

            # Save rollback state for undo capability
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="role",
                object_id=str(role_id),
                previous_state={
                    "id": previous_state.get("id"),
                    "name": previous_state.get("name"),
                    "assignedTo": previous_state.get("assignedTo"),
                    "description": previous_state.get("description"),
                    "serviceId": previous_state.get("serviceId"),
                },
            )

            try:
                role_data = await client.put(
                    "/role",
                    json=full_params,
                    resource_type="role",
                    resource_id=role_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "role_id": role_data.get("id"),
                        "name": role_data.get("name"),
                        "changes_applied": {
                            k: v for k, v in validated_params.items() if k != "id"
                        },
                    },
                )

                result = _transform_role_response(role_data)
                result["previous_state"] = {
                    "name": previous_state.get("name"),
                    "assigned_to": previous_state.get("assignedTo"),
                    "description": previous_state.get("description"),
                }
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="role", resource_id=role_id)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role", resource_id=role_id)


def _validate_role_delete_params(role_id: str | int) -> None:
    """Validate role_delete parameters (pre-flight).

    Raises ToolError if validation fails.

    Args:
        role_id: Role ID to delete (required).

    Raises:
        ToolError: If validation fails.
    """
    if not role_id:
        raise ToolError(
            "Cannot delete role: 'role_id' is required. "
            "Use 'role_list' with service_id to find valid role IDs."
        )


async def role_delete(role_id: str | int) -> dict[str, Any]:
    """Delete a BPA role.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Capture current role state for rollback
    3. Create PENDING audit record with previous_state
    4. Execute DELETE /role/{role_id} API call
    5. Update audit record to SUCCESS or FAILED

    Known Issue: The BPA server may return "Camunda publish problem" errors
    when deleting roles. This is a server-side issue related to workflow
    engine synchronization that cannot be resolved in the MCP client.
    If you encounter this error, contact your BPA administrator.

    Args:
        role_id: ID of the role to delete (required).

    Returns:
        dict: Deletion confirmation including:
            - deleted: True
            - role_id: The deleted role ID
            - deleted_role: Summary of deleted role (for rollback)
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, role not found, not authenticated,
            Camunda workflow error (server-side), or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    _validate_role_delete_params(role_id)

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Capture current state for rollback BEFORE making changes
            try:
                previous_state = await client.get(
                    "/role/{role_id}",
                    path_params={"role_id": role_id},
                    resource_type="role",
                    resource_id=role_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Role '{role_id}' not found. "
                    "Use 'role_list' with service_id to see available roles."
                )

            # Normalize previous_state to snake_case for consistency
            normalized_previous_state = {
                "id": previous_state.get("id"),
                "name": previous_state.get("name"),
                "assigned_to": previous_state.get("assignedTo"),
                "description": previous_state.get("description"),
                "service_id": previous_state.get("serviceId"),
            }

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="delete",
                object_type="role",
                object_id=str(role_id),
                params={},
            )

            # Save rollback state for undo capability (recreate on rollback)
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="role",
                object_id=str(role_id),
                previous_state={
                    "id": previous_state.get("id"),
                    "name": previous_state.get("name"),
                    "assignedTo": previous_state.get("assignedTo"),
                    "description": previous_state.get("description"),
                    "serviceId": previous_state.get("serviceId"),
                },
            )

            try:
                await client.delete(
                    "/role/{role_id}",
                    path_params={"role_id": role_id},
                    resource_type="role",
                    resource_id=role_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "deleted": True,
                        "role_id": str(role_id),
                    },
                )

                return {
                    "deleted": True,
                    "role_id": str(role_id),  # Normalize to string for consistency
                    "deleted_role": {
                        "id": normalized_previous_state["id"],
                        "name": normalized_previous_state["name"],
                        "service_id": normalized_previous_state["service_id"],
                    },
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="role", resource_id=role_id)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role", resource_id=role_id)


def register_role_tools(mcp: Any) -> None:
    """Register role tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Read operations
    mcp.tool()(role_list)
    mcp.tool()(role_get)
    # Write operations (audit-before-write pattern)
    mcp.tool()(role_create)
    mcp.tool()(role_update)
    mcp.tool()(role_delete)
