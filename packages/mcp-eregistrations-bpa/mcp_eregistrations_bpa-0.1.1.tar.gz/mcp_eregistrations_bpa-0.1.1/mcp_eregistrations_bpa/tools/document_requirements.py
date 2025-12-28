"""MCP tools for BPA document requirement operations.

This module provides tools for listing, creating, updating, and deleting
BPA document requirements. Document requirements define what documents
applicants must submit for a registration.

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED

API Endpoints used:
- GET /registration/{registration_id}/document_requirement - List requirements
- POST /registration/{registration_id}/document_requirement - Create requirement
- PUT /document_requirement - Update requirement
- DELETE /document_requirement/{id} - Delete requirement
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
    "documentrequirement_list",
    "documentrequirement_create",
    "documentrequirement_update",
    "documentrequirement_delete",
    "register_document_requirement_tools",
]


def _transform_documentrequirement_response(data: dict[str, Any]) -> dict[str, Any]:
    """Transform document requirement API response from camelCase to snake_case.

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "description": data.get("description"),
        "required": data.get("required", True),
        "registration_id": data.get("registrationId"),
    }


async def documentrequirement_list(registration_id: str | int) -> dict[str, Any]:
    """List all document requirements for a BPA registration.

    Returns document requirements configured for the specified registration.
    Each requirement includes id, name, description, and required status.

    Args:
        registration_id: The registration ID to list requirements for (required).

    Returns:
        dict: List of document requirements with total count.
            - requirements: List of document requirement objects
            - registration_id: The queried registration ID
            - total: Total number of requirements
    """
    if not registration_id:
        raise ToolError(
            "Cannot list document requirements: 'registration_id' is required. "
            "Use 'registration_list' to find valid registration IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                requirements_data = await client.get_list(
                    "/registration/{registration_id}/document_requirement",
                    path_params={"registration_id": registration_id},
                    resource_type="document_requirement",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Registration '{registration_id}' not found. "
                    "Use 'registration_list' to see available registrations."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="document_requirement")

    # Transform to consistent output format
    requirements = [
        _transform_documentrequirement_response(req) for req in requirements_data
    ]

    return {
        "requirements": requirements,
        "registration_id": registration_id,
        "total": len(requirements),
    }


def _validate_documentrequirement_create_params(
    registration_id: str | int,
    name: str,
    description: str | None,
) -> dict[str, Any]:
    """Validate documentrequirement_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        registration_id: Parent registration ID (required).
        name: Requirement name (required).
        description: Requirement description (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not registration_id:
        errors.append("'registration_id' is required")

    if not name or not name.strip():
        errors.append("'name' is required and cannot be empty")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create document requirement: {error_msg}. Check required fields."
        )

    params: dict[str, Any] = {"name": name.strip()}
    if description:
        params["description"] = description.strip()

    return params


async def documentrequirement_create(
    registration_id: str | int,
    name: str,
    description: str | None = None,
    required: bool = True,
) -> dict[str, Any]:
    """Create a new BPA document requirement for a registration.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Verify parent registration exists (no audit if not found)
    3. Create PENDING audit record
    4. Execute POST /registration/{registration_id}/document_requirement API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        registration_id: ID of the parent registration (required).
        name: Name of the document requirement (required).
        description: Description of the document requirement (optional).
        required: Whether the document is required (default: True).

    Returns:
        dict: Created document requirement details including:
            - id: The new requirement ID
            - name, description, required
            - registration_id: The parent registration ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, registration not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_documentrequirement_create_params(
        registration_id, name, description
    )
    validated_params["required"] = required

    # Get authenticated user for audit (before any API calls)
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Verify parent registration exists before creating audit record
            try:
                await client.get(
                    "/registration/{registration_id}",
                    path_params={"registration_id": registration_id},
                    resource_type="registration",
                    resource_id=registration_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Cannot create document requirement: "
                    f"Registration '{registration_id}' not found. "
                    "Use 'registration_list' to see available registrations."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="document_requirement",
                params={
                    "registration_id": str(registration_id),
                    **validated_params,
                },
            )

            try:
                requirement_data = await client.post(
                    "/registration/{registration_id}/document_requirement",
                    path_params={"registration_id": registration_id},
                    json=validated_params,
                    resource_type="document_requirement",
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "requirement_id": requirement_data.get("id"),
                        "name": requirement_data.get("name"),
                        "registration_id": str(registration_id),
                    },
                )

                result = _transform_documentrequirement_response(requirement_data)
                # Explicitly set registration_id from function parameter
                result["registration_id"] = registration_id
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="document_requirement")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="registration", resource_id=registration_id
        )


def _validate_documentrequirement_update_params(
    requirement_id: str | int,
    name: str | None,
    description: str | None,
    required: bool | None,
) -> dict[str, Any]:
    """Validate documentrequirement_update parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.

    Args:
        requirement_id: ID of requirement to update (required).
        name: New name (optional).
        description: New description (optional).
        required: New required status (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not requirement_id:
        errors.append("'requirement_id' is required")

    if name is not None and not name.strip():
        errors.append("'name' cannot be empty when provided")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    # At least one field must be provided for update
    if name is None and description is None and required is None:
        errors.append(
            "At least one field (name, description, required) must be provided"
        )

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot update document requirement: {error_msg}. Check required fields."
        )

    params: dict[str, Any] = {"id": requirement_id}
    if name is not None:
        params["name"] = name.strip()
    if description is not None:
        params["description"] = description.strip()
    if required is not None:
        params["required"] = required

    return params


async def documentrequirement_update(
    requirement_id: str | int,
    name: str | None = None,
    description: str | None = None,
    required: bool | None = None,
) -> dict[str, Any]:
    """Update an existing BPA document requirement.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Create PENDING audit record
    3. Execute PUT /document_requirement API call
    4. Update audit record to SUCCESS or FAILED

    Note: Previous state cannot be captured for rollback due to API limitations
    (no GET /document_requirement/{id} endpoint).

    Args:
        requirement_id: ID of the document requirement to update (required).
        name: New name for the requirement (optional).
        description: New description for the requirement (optional).
        required: New required status for the requirement (optional).

    Returns:
        dict: Updated document requirement details including:
            - id, name, description, required
            - registration_id: The parent registration ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, requirement not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_documentrequirement_update_params(
        requirement_id, name, description, required
    )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Note: There's no GET /document_requirement/{id} endpoint,
            # so we cannot capture previous state for rollback.
            # The PUT will fail if the requirement doesn't exist.

            # Use validated params directly - API accepts partial updates
            full_params = validated_params.copy()

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="document_requirement",
                object_id=str(requirement_id),
                params={
                    "changes": {k: v for k, v in validated_params.items() if k != "id"},
                },
            )

            try:
                requirement_data = await client.put(
                    "/document_requirement",
                    json=full_params,
                    resource_type="document_requirement",
                    resource_id=requirement_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "requirement_id": requirement_data.get("id"),
                        "name": requirement_data.get("name"),
                        "changes_applied": {
                            k: v for k, v in validated_params.items() if k != "id"
                        },
                    },
                )

                result = _transform_documentrequirement_response(requirement_data)
                # Note: previous_state not available without GET endpoint
                result["audit_id"] = audit_id
                return result

            except BPANotFoundError:
                # Mark audit as failed
                await audit_logger.mark_failed(
                    audit_id, f"Document requirement '{requirement_id}' not found"
                )
                raise ToolError(
                    f"Document requirement '{requirement_id}' not found. "
                    "Use 'documentrequirement_list' with registration_id "
                    "to see available requirements."
                )
            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(
                    e, resource_type="document_requirement", resource_id=requirement_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="document_requirement", resource_id=requirement_id
        )


def _validate_documentrequirement_delete_params(requirement_id: str | int) -> None:
    """Validate documentrequirement_delete parameters (pre-flight).

    Raises ToolError if validation fails.

    Args:
        requirement_id: Requirement ID to delete (required).

    Raises:
        ToolError: If validation fails.
    """
    if not requirement_id:
        raise ToolError(
            "Cannot delete document requirement: 'requirement_id' is required. "
            "Use 'documentrequirement_list' with registration_id "
            "to find valid requirement IDs."
        )


async def documentrequirement_delete(requirement_id: str | int) -> dict[str, Any]:
    """Delete a BPA document requirement.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Create PENDING audit record
    3. Execute DELETE /document_requirement/{id} API call
    4. Update audit record to SUCCESS or FAILED

    Note: Due to API limitations (no GET /document_requirement/{id}),
    previous state cannot be captured for rollback.

    Args:
        requirement_id: ID of the document requirement to delete (required).

    Returns:
        dict: Deletion confirmation including:
            - deleted: True
            - requirement_id: The deleted requirement ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, requirement not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    _validate_documentrequirement_delete_params(requirement_id)

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Create audit record BEFORE API call (audit-before-write pattern)
            # Note: Cannot capture previous state - no GET endpoint
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="delete",
                object_type="document_requirement",
                object_id=str(requirement_id),
                params={},
            )

            try:
                await client.delete(
                    "/document_requirement/{id}",
                    path_params={"id": requirement_id},
                    resource_type="document_requirement",
                    resource_id=requirement_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "deleted": True,
                        "requirement_id": str(requirement_id),
                    },
                )

                return {
                    "deleted": True,
                    "requirement_id": str(requirement_id),
                    "audit_id": audit_id,
                }

            except BPANotFoundError:
                # Mark audit as failed
                await audit_logger.mark_failed(
                    audit_id, f"Document requirement '{requirement_id}' not found"
                )
                raise ToolError(
                    f"Document requirement '{requirement_id}' not found. "
                    "Use 'documentrequirement_list' with registration_id "
                    "to see available requirements."
                )
            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(
                    e, resource_type="document_requirement", resource_id=requirement_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="document_requirement", resource_id=requirement_id
        )


def register_document_requirement_tools(mcp: Any) -> None:
    """Register document requirement tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Read operations
    mcp.tool()(documentrequirement_list)
    # Write operations (audit-before-write pattern)
    mcp.tool()(documentrequirement_create)
    mcp.tool()(documentrequirement_update)
    mcp.tool()(documentrequirement_delete)
