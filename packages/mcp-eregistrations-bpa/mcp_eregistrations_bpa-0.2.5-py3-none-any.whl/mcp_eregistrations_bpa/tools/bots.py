"""MCP tools for BPA bot operations.

This module provides tools for listing, retrieving, creating, and updating BPA bots.
Bots are workflow automation entities that execute actions on form components.

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED

API Endpoints used:
- GET /service/{service_id}/bot - List bots for a service
- GET /bot/{bot_id} - Get bot by ID
- POST /service/{service_id}/bot - Create bot within service
- PUT /bot - Update bot
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
    "bot_list",
    "bot_get",
    "bot_create",
    "bot_update",
    "register_bot_tools",
]


def _transform_bot_response(data: dict[str, Any]) -> dict[str, Any]:
    """Transform bot API response from camelCase to snake_case.

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "bot_type": data.get("botType"),
        "description": data.get("description"),
        "enabled": data.get("enabled", True),
        "service_id": data.get("serviceId"),
    }


async def bot_list(service_id: str | int) -> dict[str, Any]:
    """List all bots for a BPA service.

    Returns bots configured for the specified service.
    Each bot includes id, name, bot_type, and enabled status.

    Args:
        service_id: The service ID to list bots for (required).

    Returns:
        dict: List of bots with total count.
            - bots: List of bot objects
            - service_id: The queried service ID
            - total: Total number of bots
    """
    if not service_id:
        raise ToolError(
            "Cannot list bots: 'service_id' is required. "
            "Use 'service_list' to find valid service IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                bots_data = await client.get_list(
                    "/service/{service_id}/bot",
                    path_params={"service_id": service_id},
                    resource_type="bot",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="bot")

    # Transform to consistent output format
    bots = [_transform_bot_response(bot) for bot in bots_data]

    return {
        "bots": bots,
        "service_id": service_id,
        "total": len(bots),
    }


async def bot_get(bot_id: str | int) -> dict[str, Any]:
    """Get details of a BPA bot by ID.

    Returns complete bot details including configuration.

    Args:
        bot_id: The unique identifier of the bot.

    Returns:
        dict: Complete bot details including:
            - id, name, bot_type, description, enabled
            - service_id: The parent service ID
    """
    if not bot_id:
        raise ToolError(
            "Cannot get bot: 'bot_id' is required. "
            "Use 'bot_list' with service_id to find valid bot IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                bot_data = await client.get(
                    "/bot/{bot_id}",
                    path_params={"bot_id": bot_id},
                    resource_type="bot",
                    resource_id=bot_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Bot '{bot_id}' not found. "
                    "Use 'bot_list' with service_id to see available bots."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="bot", resource_id=bot_id)

    return _transform_bot_response(bot_data)


def _validate_bot_create_params(
    service_id: str | int,
    bot_type: str,
    name: str,
    description: str | None,
) -> dict[str, Any]:
    """Validate bot_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        bot_type: Bot type identifier (required).
        name: Bot name (required).
        description: Bot description (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not service_id:
        errors.append("'service_id' is required")

    if not bot_type or not str(bot_type).strip():
        errors.append("'bot_type' is required")

    if not name or not name.strip():
        errors.append("'name' is required and cannot be empty")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot create bot: {error_msg}. Check required fields.")

    params: dict[str, Any] = {
        "botType": str(bot_type).strip(),
        "name": name.strip(),
        "enabled": True,
    }
    if description:
        params["description"] = description.strip()

    return params


async def bot_create(
    service_id: str | int,
    bot_type: str,
    name: str,
    description: str | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    """Create a new BPA bot within a service.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Verify parent service exists (no audit if service not found)
    3. Create PENDING audit record
    4. Execute POST /service/{service_id}/bot API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        service_id: ID of the parent service (required).
        bot_type: Type of bot to create (required).
        name: Name of the bot (required).
        description: Description of the bot (optional).
        enabled: Whether the bot is enabled (default: True).

    Returns:
        dict: Created bot details including:
            - id: The new bot ID
            - name, bot_type, description, enabled
            - service_id: The parent service ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, service not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_bot_create_params(
        service_id, bot_type, name, description
    )
    validated_params["enabled"] = enabled

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
                    f"Cannot create bot: Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="bot",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                bot_data = await client.post(
                    "/service/{service_id}/bot",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="bot",
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "bot_id": bot_data.get("id"),
                        "name": bot_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                result = _transform_bot_response(bot_data)
                result["service_id"] = service_id  # Ensure service_id is always set
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="bot")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


def _validate_bot_update_params(
    bot_id: str | int,
    name: str | None,
    description: str | None,
    enabled: bool | None,
) -> dict[str, Any]:
    """Validate bot_update parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.

    Args:
        bot_id: ID of bot to update (required).
        name: New name (optional).
        description: New description (optional).
        enabled: New enabled status (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not bot_id:
        errors.append("'bot_id' is required")

    if name is not None and not name.strip():
        errors.append("'name' cannot be empty when provided")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    # At least one field must be provided for update
    if name is None and description is None and enabled is None:
        errors.append(
            "At least one field (name, description, enabled) must be provided"
        )

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot update bot: {error_msg}. Check required fields.")

    params: dict[str, Any] = {"id": bot_id}
    if name is not None:
        params["name"] = name.strip()
    if description is not None:
        params["description"] = description.strip()
    if enabled is not None:
        params["enabled"] = enabled

    return params


async def bot_update(
    bot_id: str | int,
    name: str | None = None,
    description: str | None = None,
    enabled: bool | None = None,
) -> dict[str, Any]:
    """Update an existing BPA bot.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Capture current state for rollback
    3. Create PENDING audit record
    4. Execute PUT /bot API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        bot_id: ID of the bot to update (required).
        name: New name for the bot (optional).
        description: New description for the bot (optional).
        enabled: New enabled status for the bot (optional).

    Returns:
        dict: Updated bot details including:
            - id, name, bot_type, description, enabled
            - service_id: The parent service ID
            - previous_state: The state before update (for rollback reference)
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, bot not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_bot_update_params(bot_id, name, description, enabled)

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
                    "/bot/{bot_id}",
                    path_params={"bot_id": bot_id},
                    resource_type="bot",
                    resource_id=bot_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Bot '{bot_id}' not found. "
                    "Use 'bot_list' with service_id to see available bots."
                )

            # Merge provided changes with current state for full object PUT
            full_params = {
                "id": bot_id,
                "name": validated_params.get("name", previous_state.get("name")),
                "botType": previous_state.get("botType"),
                "description": validated_params.get(
                    "description", previous_state.get("description")
                ),
                "enabled": validated_params.get(
                    "enabled", previous_state.get("enabled", True)
                ),
                "serviceId": previous_state.get("serviceId"),
            }

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="bot",
                object_id=str(bot_id),
                params={
                    "changes": validated_params,
                    "previous_state": {
                        "name": previous_state.get("name"),
                        "description": previous_state.get("description"),
                        "enabled": previous_state.get("enabled"),
                    },
                },
            )

            try:
                bot_data = await client.put(
                    "/bot",
                    json=full_params,
                    resource_type="bot",
                    resource_id=bot_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "bot_id": bot_data.get("id"),
                        "name": bot_data.get("name"),
                        "changes_applied": {
                            k: v for k, v in validated_params.items() if k != "id"
                        },
                    },
                )

                result = _transform_bot_response(bot_data)
                result["previous_state"] = {
                    "name": previous_state.get("name"),
                    "description": previous_state.get("description"),
                    "enabled": previous_state.get("enabled"),
                }
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="bot", resource_id=bot_id)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="bot", resource_id=bot_id)


def register_bot_tools(mcp: Any) -> None:
    """Register bot tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Read operations
    mcp.tool()(bot_list)
    mcp.tool()(bot_get)
    # Write operations (audit-before-write pattern)
    mcp.tool()(bot_create)
    mcp.tool()(bot_update)
