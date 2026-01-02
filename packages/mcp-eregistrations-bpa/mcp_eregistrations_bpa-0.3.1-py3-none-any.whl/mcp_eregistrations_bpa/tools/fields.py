"""MCP tools for BPA field operations.

This module provides tools for listing and retrieving BPA form fields.
Fields are accessed through service endpoints (service-centric API design).
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.bpa_client import BPAClient
from mcp_eregistrations_bpa.bpa_client.errors import (
    BPAClientError,
    BPANotFoundError,
    translate_error,
)

__all__ = ["field_list", "field_get", "register_field_tools"]


async def field_list(service_id: str | int) -> dict[str, Any]:
    """List all fields for a service.

    Returns all fields for the specified service with summary info.
    Each field includes key, name, type, required status, and component info.

    Args:
        service_id: The service ID to list fields for.

    Returns:
        dict: List of fields with total count.
            - fields: List of field objects
            - total: Total number of fields
    """
    try:
        async with BPAClient() as client:
            fields_data = await client.get_list(
                "/service/{service_id}/fields",
                path_params={"service_id": service_id},
                resource_type="field",
            )
    except BPAClientError as e:
        raise translate_error(e, resource_type="field")

    # Transform to consistent output format with snake_case keys
    fields = []
    for field in fields_data:
        fields.append(
            {
                "key": field.get("key"),
                "name": field.get("name"),
                "type": field.get("type"),
                "required": field.get("required", False),
                "component_key": field.get("componentKey"),
                "label": field.get("label"),
            }
        )

    return {
        "fields": fields,
        "total": len(fields),
        "service_id": service_id,
    }


async def field_get(service_id: str | int, field_key: str) -> dict[str, Any]:
    """Get details of a BPA field by service ID and field key.

    Returns complete field details for a specific field within a service.

    Args:
        service_id: The service containing the field.
        field_key: The field key/identifier within the service.

    Returns:
        dict: Complete field details including:
            - key, name, label, type, required
            - component_key: The form component containing this field
            - validation info if available
    """
    try:
        async with BPAClient() as client:
            try:
                field_data = await client.get(
                    "/service/{service_id}/fields/{field_key}",
                    path_params={"service_id": service_id, "field_key": field_key},
                    resource_type="field",
                    resource_id=field_key,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Field '{field_key}' not found in service '{service_id}'. "
                    "Use 'field_list' with the service_id to see available fields."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="field", resource_id=field_key)

    return {
        "key": field_data.get("key"),
        "name": field_data.get("name"),
        "label": field_data.get("label"),
        "type": field_data.get("type"),
        "required": field_data.get("required", False),
        "component_key": field_data.get("componentKey"),
        "service_id": service_id,
    }


def register_field_tools(mcp: Any) -> None:
    """Register field tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(field_list)
    mcp.tool()(field_get)
