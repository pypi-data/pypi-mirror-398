"""Service analysis tools for BPA API.

This module provides MCP tools for analyzing BPA services.
Note: The BPA API is service-centric and does not support cross-object
relationship queries. Analysis is limited to service-level data.

Tools:
    analyze_service: Analyze a BPA service with AI-optimized output
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
    "analyze_service",
    "register_analysis_tools",
]


def _transform_summary(item: dict[str, Any]) -> dict[str, Any]:
    """Transform an item to a summary with id/key and name."""
    return {
        "id": item.get("id"),
        "key": item.get("key"),
        "name": item.get("name"),
    }


def _calculate_complexity_score(
    registration_count: int,
    field_count: int,
    determinant_count: int,
) -> str:
    """Calculate service complexity score.

    Scoring criteria:
    - low: ≤5 registrations, ≤20 fields, ≤5 determinants
    - medium: ≤15 registrations, ≤50 fields, ≤20 determinants
    - high: Exceeds medium thresholds

    Args:
        registration_count: Number of registrations in the service.
        field_count: Number of fields in the service.
        determinant_count: Number of determinants in the service.

    Returns:
        Complexity level: "low", "medium", or "high".
    """
    if registration_count <= 5 and field_count <= 20 and determinant_count <= 5:
        return "low"
    elif registration_count <= 15 and field_count <= 50 and determinant_count <= 20:
        return "medium"
    else:
        return "high"


def _build_service_overview(
    service_data: dict[str, Any],
    registrations: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    determinants: list[dict[str, Any]],
    forms: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build service overview with counts for AI reasoning.

    Args:
        service_data: Service metadata from API.
        registrations: List of registrations.
        fields: List of fields.
        determinants: List of determinants.
        forms: List of forms.

    Returns:
        Overview dictionary with status, counts, and complexity score.
    """
    return {
        "status": service_data.get("status", "active"),
        "total_registrations": len(registrations),
        "total_fields": len(fields),
        "total_determinants": len(determinants),
        "total_forms": len(forms),
        "complexity_score": _calculate_complexity_score(
            len(registrations), len(fields), len(determinants)
        ),
    }


def _generate_insights(overview: dict[str, Any]) -> list[str]:
    """Generate actionable insights for AI reasoning.

    Args:
        overview: Service overview data.

    Returns:
        List of insight strings.
    """
    insights: list[str] = []

    # Complexity insight
    complexity = overview.get("complexity_score", "low")
    total_fields = overview.get("total_fields", 0)
    total_determinants = overview.get("total_determinants", 0)
    total_registrations = overview.get("total_registrations", 0)

    if complexity == "high":
        insights.append("Service has high complexity - consider modular restructuring")
    elif complexity == "medium":
        insights.append("Service has moderate complexity")
    else:
        insights.append("Service has low complexity - well organized")

    # Field insights
    if total_fields > 50:
        insights.append(f"Service has {total_fields} fields - review for consolidation")

    # Determinant insights
    if total_determinants > 20:
        insights.append(
            f"Service has {total_determinants} determinants - "
            "complex business rules present"
        )
    elif total_determinants == 0:
        insights.append("No determinants - all fields are always visible")

    # Registration insights
    if total_registrations > 10:
        insights.append(
            f"Service has {total_registrations} registrations - "
            "consider grouping related ones"
        )
    elif total_registrations == 0:
        insights.append("No registrations defined yet")

    return insights


async def analyze_service(service_id: str | int) -> dict[str, Any]:
    """Analyze a BPA service with AI-optimized output.

    Provides comprehensive analysis including overview, entity lists,
    and actionable insights formatted for AI consumption.

    Note: The BPA API is service-centric. Cross-object relationships
    (e.g., which fields use which determinants) are not queryable.
    Use this tool to understand service structure and complexity.

    Args:
        service_id: The unique identifier of the service.

    Returns:
        dict: AI-optimized service analysis including:
            - service_id: The service ID
            - service_name: The service name
            - overview: Service metadata and counts
            - registrations: List of registration summaries
            - fields: List of field summaries with keys
            - determinants: List of determinant summaries
            - forms: List of form summaries
            - insights: Actionable recommendations
    """
    try:
        async with BPAClient() as client:
            try:
                # Get service details
                service_data = await client.get(
                    "/service/{id}",
                    path_params={"id": service_id},
                    resource_type="service",
                    resource_id=service_id,
                )

                # Get child objects using correct service-scoped endpoints
                registrations = await client.get_list(
                    "/service/{service_id}/registrations",
                    path_params={"service_id": service_id},
                    resource_type="registration",
                )

                fields = await client.get_list(
                    "/service/{service_id}/fields",
                    path_params={"service_id": service_id},
                    resource_type="field",
                )

                determinants = await client.get_list(
                    "/service/{service_id}/determinant",
                    path_params={"service_id": service_id},
                    resource_type="determinant",
                )

                forms = await client.get_list(
                    "/service/{service_id}/form",
                    path_params={"service_id": service_id},
                    resource_type="form",
                )

                # Build AI-optimized response
                overview = _build_service_overview(
                    service_data, registrations, fields, determinants, forms
                )

                insights = _generate_insights(overview)

                return {
                    "service_id": service_id,
                    "service_name": service_data.get("name", ""),
                    "description": service_data.get("description", ""),
                    "overview": overview,
                    "registrations": [
                        {"id": r.get("id"), "name": r.get("name")}
                        for r in registrations
                    ],
                    "fields": [
                        {
                            "key": f.get("key"),
                            "name": f.get("name"),
                            "type": f.get("type"),
                            "component_key": f.get("componentKey"),
                        }
                        for f in fields
                    ],
                    "determinants": [
                        {
                            "id": d.get("id"),
                            "name": d.get("name"),
                            "type": d.get("type"),
                        }
                        for d in determinants
                    ],
                    "forms": [
                        {"id": f.get("id"), "name": f.get("name")} for f in forms
                    ],
                    "insights": insights,
                }

            except BPANotFoundError:
                raise ToolError(
                    f"Service {service_id} not found. "
                    "Use 'service_list' to see available services."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


def register_analysis_tools(mcp: Any) -> None:
    """Register analysis tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(analyze_service)
