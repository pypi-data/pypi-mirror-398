"""BPA API endpoint constants.

This module defines all BPA API v3 (2016/06) endpoint URL patterns.
Endpoints use string formatting for path parameters.

Usage:
    from mcp_eregistrations_bpa.bpa_client.endpoints import SERVICES, SERVICE_BY_ID

    url = SERVICES  # "/service"
    url = SERVICE_BY_ID.format(id=123)  # "/service/123"
"""

from __future__ import annotations

__all__ = [
    # Service endpoints
    "SERVICES",
    "SERVICE_BY_ID",
    "SERVICE_FIELDS",
    "SERVICE_DETERMINANTS",
    "SERVICE_FORMS",
    "SERVICE_ROLES",
    "SERVICE_REGISTRATIONS",
    # Registration endpoints
    "REGISTRATIONS",
    "REGISTRATION_BY_ID",
    "REGISTRATION_FIELDS",
    "REGISTRATION_DETERMINANTS",
    "REGISTRATION_COSTS",
    "REGISTRATION_DOCUMENTS",
    # Form endpoints
    "FORMS",
    "FORM_BY_ID",
    "FORM_FIELDS",
    "FORM_DETERMINANTS",
    # Field endpoints
    "FIELDS",
    "FIELD_BY_ID",
    "FIELD_DETERMINANTS",
    "FIELD_REGISTRATIONS",
    # Determinant endpoints
    "DETERMINANTS",
    "DETERMINANT_BY_ID",
    "DETERMINANT_FIELDS",
    "DETERMINANT_REGISTRATIONS",
    # Role endpoints
    "ROLES",
    "ROLE_BY_ID",
    # Cost endpoints
    "COSTS",
    "COST_BY_ID",
    # Document endpoints
    "DOCUMENTS",
    "DOCUMENT_BY_ID",
    # Component Actions endpoints
    "COMPONENT_ACTIONS_BY_ID",
    "SERVICE_COMPONENT_ACTIONS",
]

# =============================================================================
# Service Endpoints
# =============================================================================

#: List all services
SERVICES = "/service"

#: Get/update/delete service by ID
SERVICE_BY_ID = "/service/{id}"

#: Fields for a specific service
SERVICE_FIELDS = "/service/{service_id}/fields"

#: Determinants for a specific service
SERVICE_DETERMINANTS = "/service/{service_id}/determinant"

#: Forms for a specific service
SERVICE_FORMS = "/service/{service_id}/form"

#: Roles for a specific service
SERVICE_ROLES = "/service/{service_id}/roles"

#: Registrations for a specific service
SERVICE_REGISTRATIONS = "/service/{service_id}/registrations"

# =============================================================================
# Registration Endpoints
# =============================================================================

#: List all registrations
REGISTRATIONS = "/registration"

#: Get/update/delete registration by ID
REGISTRATION_BY_ID = "/registration/{registration_id}"

#: Fields for a specific registration
REGISTRATION_FIELDS = "/registration/{registration_id}/fields"

#: Determinants for a specific registration
REGISTRATION_DETERMINANTS = "/registration/{registration_id}/determinants"

#: Costs for a specific registration
REGISTRATION_COSTS = "/registration/{registration_id}/costs"

#: Documents for a specific registration
REGISTRATION_DOCUMENTS = "/registration/{registration_id}/documents"

# =============================================================================
# Form Endpoints
# =============================================================================

#: List all forms
FORMS = "/form"

#: Get/update/delete form by ID
FORM_BY_ID = "/form/{form_id}"

#: Fields for a specific form
FORM_FIELDS = "/form/{form_id}/fields"

#: Determinants for a specific form
FORM_DETERMINANTS = "/form/{form_id}/determinants"

# =============================================================================
# Field Endpoints
# =============================================================================

#: List all fields
FIELDS = "/field"

#: Get/update/delete field by ID
FIELD_BY_ID = "/field/{field_id}"

#: Determinants linked to a field (many-to-many)
FIELD_DETERMINANTS = "/field/{field_id}/determinants"

#: Registrations linked to a field (many-to-many)
FIELD_REGISTRATIONS = "/field/{field_id}/registrations"

# =============================================================================
# Determinant Endpoints
# =============================================================================

#: List all determinants
DETERMINANTS = "/determinant"

#: Get/update/delete determinant by ID
DETERMINANT_BY_ID = "/determinant/{determinant_id}"

#: Fields linked to a determinant (many-to-many)
DETERMINANT_FIELDS = "/determinant/{determinant_id}/fields"

#: Registrations linked to a determinant (many-to-many)
DETERMINANT_REGISTRATIONS = "/determinant/{determinant_id}/registrations"

# =============================================================================
# Role Endpoints
# =============================================================================

#: List all roles
ROLES = "/role"

#: Get/update/delete role by ID
ROLE_BY_ID = "/role/{role_id}"

# =============================================================================
# Cost Endpoints
# =============================================================================

#: List all costs
COSTS = "/cost"

#: Get/update/delete cost by ID
COST_BY_ID = "/cost/{cost_id}"

# =============================================================================
# Document Endpoints
# =============================================================================

#: List all documents
DOCUMENTS = "/document"

#: Get/update/delete document by ID
DOCUMENT_BY_ID = "/document/{document_id}"

# =============================================================================
# Component Actions Endpoints
# =============================================================================

#: Get/update component actions by ID
COMPONENT_ACTIONS_BY_ID = "/componentactions/{id}"

#: Get/update/delete component actions for a specific service component
SERVICE_COMPONENT_ACTIONS = "/service/{service_id}/componentactions/{component_key}"
