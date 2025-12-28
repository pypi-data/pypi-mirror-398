"""MCP tools for BPA operations.

This module provides tools for interacting with the BPA API through MCP.
"""

from mcp_eregistrations_bpa.tools.actions import (
    componentaction_get,
    componentaction_get_by_component,
    register_action_tools,
)
from mcp_eregistrations_bpa.tools.analysis import (
    analyze_service,
    register_analysis_tools,
)
from mcp_eregistrations_bpa.tools.audit import (
    audit_get,
    audit_list,
    register_audit_tools,
)
from mcp_eregistrations_bpa.tools.bots import (
    bot_create,
    bot_get,
    bot_list,
    bot_update,
    register_bot_tools,
)
from mcp_eregistrations_bpa.tools.costs import (
    cost_create_fixed,
    cost_create_formula,
    cost_delete,
    cost_update,
    register_cost_tools,
)
from mcp_eregistrations_bpa.tools.determinants import (
    determinant_get,
    determinant_list,
    register_determinant_tools,
)
from mcp_eregistrations_bpa.tools.document_requirements import (
    documentrequirement_create,
    documentrequirement_delete,
    documentrequirement_list,
    documentrequirement_update,
    register_document_requirement_tools,
)
from mcp_eregistrations_bpa.tools.fields import (
    field_get,
    field_list,
    register_field_tools,
)
from mcp_eregistrations_bpa.tools.registrations import (
    register_registration_tools,
    registration_get,
    registration_list,
)
from mcp_eregistrations_bpa.tools.roles import (
    register_role_tools,
    role_create,
    role_delete,
    role_get,
    role_list,
    role_update,
)
from mcp_eregistrations_bpa.tools.rollback import (
    register_rollback_tools,
    rollback,
    rollback_history,
)
from mcp_eregistrations_bpa.tools.services import (
    register_service_tools,
    service_get,
    service_list,
)

__all__ = [
    # Service tools
    "service_list",
    "service_get",
    "register_service_tools",
    # Registration tools
    "registration_list",
    "registration_get",
    "register_registration_tools",
    # Field tools
    "field_list",
    "field_get",
    "register_field_tools",
    # Determinant tools
    "determinant_list",
    "determinant_get",
    "register_determinant_tools",
    # Component action tools
    "componentaction_get",
    "componentaction_get_by_component",
    "register_action_tools",
    # Bot tools
    "bot_list",
    "bot_get",
    "bot_create",
    "bot_update",
    "register_bot_tools",
    # Role tools
    "role_list",
    "role_get",
    "role_create",
    "role_update",
    "role_delete",
    "register_role_tools",
    # Analysis tools
    "analyze_service",
    "register_analysis_tools",
    # Document requirement tools
    "documentrequirement_list",
    "documentrequirement_create",
    "documentrequirement_update",
    "documentrequirement_delete",
    "register_document_requirement_tools",
    # Cost tools
    "cost_create_fixed",
    "cost_create_formula",
    "cost_update",
    "cost_delete",
    "register_cost_tools",
    # Audit tools
    "audit_list",
    "audit_get",
    "register_audit_tools",
    # Rollback tools
    "rollback",
    "rollback_history",
    "register_rollback_tools",
]
