"""Component action tools for BPA API.

This module provides MCP tools for retrieving component actions
from the BPA API. Component actions define workflow automation
configured for form components.

Tools:
    componentaction_get: Get component actions by ID
    componentaction_get_by_component: Get actions for a form component
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

__all__ = [
    "componentaction_get",
    "componentaction_get_by_component",
    "register_action_tools",
]


async def componentaction_get(id: str) -> dict[str, Any]:
    """Get component actions by ID.

    Returns the complete FormComponentActions record including all action rows
    with their bot configurations and execution parameters.

    Args:
        id: The unique identifier of the component actions record.

    Returns:
        dict: Complete component actions including:
            - id: Unique identifier
            - service_id: Parent service ID
            - component_key: Form component key
            - actions: List of action rows with bot configurations
    """
    try:
        async with BPAClient() as client:
            try:
                data = await client.get(
                    "/componentactions/{id}",
                    path_params={"id": id},
                    resource_type="componentactions",
                    resource_id=id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"ComponentActions '{id}' not found. Verify the ID is correct."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="componentactions", resource_id=id)

    return _transform_component_actions(data)


async def componentaction_get_by_component(
    service_id: str | int, component_key: str
) -> dict[str, Any]:
    """Get component actions for a specific form component.

    Returns the FormComponentActions configured for a component within a service.

    Args:
        service_id: The service containing the component.
        component_key: The form component key/identifier.

    Returns:
        dict: Component actions for the specified component including:
            - id: Unique identifier
            - service_id: Parent service ID
            - component_key: Form component key
            - actions: List of action rows with bot configurations
    """
    try:
        async with BPAClient() as client:
            try:
                data = await client.get(
                    "/service/{service_id}/componentactions/{component_key}",
                    path_params={
                        "service_id": service_id,
                        "component_key": component_key,
                    },
                    resource_type="componentactions",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"No actions found for component '{component_key}' "
                    f"in service '{service_id}'."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="componentactions")

    return _transform_component_actions(data)


def _transform_bot(bot: dict[str, Any]) -> dict[str, Any]:
    """Transform a bot object from camelCase to snake_case.

    Args:
        bot: Raw bot object from API.

    Returns:
        dict: Transformed bot with snake_case keys.
    """
    return {
        "bot_type": bot.get("botType"),
        "name": bot.get("name"),
        "description": bot.get("description"),
        "enabled": bot.get("enabled", True),
    }


def _transform_component_actions(data: dict[str, Any]) -> dict[str, Any]:
    """Transform API response to snake_case format.

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    actions = []
    for action in data.get("actions", []):
        bots = [_transform_bot(bot) for bot in action.get("bots", [])]
        actions.append(
            {
                "id": action.get("id"),
                "json_determinants": action.get("jsonDeterminants"),
                "bots": bots,
                "sort_order": action.get("sortOrderNumber"),
                "parallel": action.get("parallel", False),
                "mandatory": action.get("mandatory", False),
                "multiple_bot": action.get("multipleBot", False),
                "multiple_field_key": action.get("multipleFieldKey"),
            }
        )

    return {
        "id": data.get("id"),
        "service_id": data.get("serviceId"),
        "component_key": data.get("componentKey"),
        "actions": actions,
    }


def register_action_tools(mcp: Any) -> None:
    """Register action tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(componentaction_get)
    mcp.tool()(componentaction_get_by_component)
