"""MCP tools for BPA determinant operations.

This module provides tools for listing, retrieving, creating, and updating
BPA determinants. Determinants are accessed through service endpoints
(service-centric API design).

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED

API Endpoints used:
- GET /service/{service_id}/determinant - List determinants for service
- GET /determinant/{id} - Get determinant by ID
- POST /service/{service_id}/textdeterminant - Create text determinant
- PUT /service/{service_id}/textdeterminant - Update text determinant
- POST /service/{service_id}/selectdeterminant - Create select determinant
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
    "determinant_list",
    "determinant_get",
    "textdeterminant_create",
    "textdeterminant_update",
    "selectdeterminant_create",
    "register_determinant_tools",
]


async def determinant_list(service_id: str | int) -> dict[str, Any]:
    """List all determinants for a service.

    Returns determinants for the specified service with summary info.
    Each determinant includes id, name, type, and condition summary.

    Args:
        service_id: The service ID to list determinants for.

    Returns:
        dict: List of determinants with total count.
            - determinants: List of determinant objects
            - total: Total number of determinants
            - service_id: The service these determinants belong to
    """
    try:
        async with BPAClient() as client:
            determinants_data = await client.get_list(
                "/service/{service_id}/determinant",
                path_params={"service_id": service_id},
                resource_type="determinant",
            )
    except BPAClientError as e:
        raise translate_error(e, resource_type="determinant")

    # Transform to consistent output format with snake_case keys
    determinants = []
    for det in determinants_data:
        determinants.append(
            {
                "id": det.get("id"),
                "name": det.get("name"),
                "type": det.get("type"),
                "condition_summary": det.get("conditionSummary"),
                "json_condition": det.get("jsonCondition"),
            }
        )

    return {
        "determinants": determinants,
        "total": len(determinants),
        "service_id": service_id,
    }


async def determinant_get(determinant_id: str | int) -> dict[str, Any]:
    """Get details of a BPA determinant by ID.

    Returns complete determinant details including condition logic.
    Note: Related fields/actions are not available via this endpoint.

    Args:
        determinant_id: The unique identifier of the determinant.

    Returns:
        dict: Complete determinant details including:
            - id, name, type
            - condition_logic: The condition definition
            - json_condition: JSON representation of the condition
    """
    try:
        async with BPAClient() as client:
            try:
                determinant_data = await client.get(
                    "/determinant/{id}",
                    path_params={"id": determinant_id},
                    resource_type="determinant",
                    resource_id=determinant_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Determinant '{determinant_id}' not found. "
                    "Use 'determinant_list' with service_id to see determinants."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="determinant", resource_id=determinant_id
        )

    return {
        "id": determinant_data.get("id"),
        "name": determinant_data.get("name"),
        "type": determinant_data.get("type"),
        "condition_logic": determinant_data.get("conditionLogic"),
        "json_condition": determinant_data.get("jsonCondition"),
        "condition_summary": determinant_data.get("conditionSummary"),
    }


def _validate_textdeterminant_create_params(
    service_id: str | int,
    name: str,
    operator: str,
    target_form_field_key: str,
) -> dict[str, Any]:
    """Validate textdeterminant_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Determinant name (required).
        operator: Comparison operator (required). Valid values: equals, notEquals,
            contains, notContains, startsWith, endsWith, isEmpty, isNotEmpty.
        target_form_field_key: The form field key this determinant targets (required).

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

    if not operator or not operator.strip():
        errors.append("'operator' is required")

    valid_operators = [
        "equals",
        "notEquals",
        "contains",
        "notContains",
        "startsWith",
        "endsWith",
        "isEmpty",
        "isNotEmpty",
    ]
    if operator and operator.strip() not in valid_operators:
        errors.append(f"'operator' must be one of: {', '.join(valid_operators)}")

    if not target_form_field_key or not target_form_field_key.strip():
        errors.append("'target_form_field_key' is required")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create text determinant: {error_msg}. "
            "Provide valid 'service_id', 'name', 'operator', and "
            "'target_form_field_key' parameters."
        )

    return {
        "name": name.strip(),
        "operator": operator.strip(),
        "targetFormFieldKey": target_form_field_key.strip(),
    }


def _validate_textdeterminant_update_params(
    service_id: str | int,
    determinant_id: str | int,
    name: str | None,
    operator: str | None,
    target_form_field_key: str | None,
    condition_logic: str | None,
    json_condition: str | None,
) -> dict[str, Any]:
    """Validate textdeterminant_update parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.

    Args:
        service_id: Parent service ID (required).
        determinant_id: Determinant ID to update (required).
        name: New name (optional).
        operator: Comparison operator (optional). Valid values: equals, notEquals,
            contains, notContains, startsWith, endsWith, isEmpty, isNotEmpty.
        target_form_field_key: The form field key this determinant targets (optional).
        condition_logic: New condition logic (optional).
        json_condition: New JSON condition (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not service_id:
        errors.append("'service_id' is required")

    if not determinant_id:
        errors.append("'determinant_id' is required")

    if name is not None and not name.strip():
        errors.append("'name' cannot be empty when provided")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    valid_operators = [
        "equals",
        "notEquals",
        "contains",
        "notContains",
        "startsWith",
        "endsWith",
        "isEmpty",
        "isNotEmpty",
    ]
    if operator is not None:
        if not operator.strip():
            errors.append("'operator' cannot be empty when provided")
        elif operator.strip() not in valid_operators:
            errors.append(f"'operator' must be one of: {', '.join(valid_operators)}")

    if target_form_field_key is not None and not target_form_field_key.strip():
        errors.append("'target_form_field_key' cannot be empty when provided")

    # At least one field must be provided for update
    if all(
        v is None
        for v in [
            name,
            operator,
            target_form_field_key,
            condition_logic,
            json_condition,
        ]
    ):
        errors.append(
            "At least one field (name, operator, target_form_field_key, "
            "condition_logic, json_condition) required"
        )

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot update text determinant: {error_msg}. Check required fields."
        )

    params: dict[str, Any] = {"id": determinant_id}
    if name is not None:
        params["name"] = name.strip()
    if operator is not None:
        params["operator"] = operator.strip()
    if target_form_field_key is not None:
        params["targetFormFieldKey"] = target_form_field_key.strip()
    if condition_logic is not None:
        params["conditionLogic"] = condition_logic
    if json_condition is not None:
        params["jsonCondition"] = json_condition

    return params


def _validate_selectdeterminant_create_params(
    service_id: str | int,
    name: str,
    operator: str,
    select_value: str,
) -> dict[str, Any]:
    """Validate selectdeterminant_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Determinant name (required).
        operator: Comparison operator (required). Valid values: equals, notEquals,
            contains, notContains, startsWith, endsWith, isEmpty, isNotEmpty.
        select_value: The select option value this determinant matches (required).

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

    if not operator or not operator.strip():
        errors.append("'operator' is required")

    valid_operators = [
        "equals",
        "notEquals",
        "contains",
        "notContains",
        "startsWith",
        "endsWith",
        "isEmpty",
        "isNotEmpty",
    ]
    if operator and operator.strip() not in valid_operators:
        errors.append(f"'operator' must be one of: {', '.join(valid_operators)}")

    if not select_value or not select_value.strip():
        errors.append("'select_value' is required")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create select determinant: {error_msg}. "
            "Provide valid 'service_id', 'name', 'operator', and "
            "'select_value' parameters."
        )

    return {
        "name": name.strip(),
        "operator": operator.strip(),
        "selectValue": select_value.strip(),
    }


async def textdeterminant_create(
    service_id: str | int,
    name: str,
    operator: str,
    target_form_field_key: str,
    condition_logic: str | None = None,
    json_condition: str | None = None,
) -> dict[str, Any]:
    """Create a new text determinant within a service.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Verify parent service exists (no audit if service not found)
    3. Create PENDING audit record
    4. Execute POST /service/{service_id}/textdeterminant API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        service_id: ID of the parent service (required).
        name: Name of the determinant (required).
        operator: Comparison operator (required). Valid values: equals, notEquals,
            contains, notContains, startsWith, endsWith, isEmpty, isNotEmpty.
        target_form_field_key: The form field key this determinant targets (required).
        condition_logic: Condition logic expression (optional).
        json_condition: JSON representation of the condition (optional).

    Returns:
        dict: Created determinant details including:
            - id: The new determinant ID
            - name, type, operator, target_form_field_key
            - condition_logic, json_condition
            - service_id: The parent service ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, service not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_textdeterminant_create_params(
        service_id, name, operator, target_form_field_key
    )

    # Add optional parameters
    if condition_logic is not None:
        validated_params["conditionLogic"] = condition_logic
    if json_condition is not None:
        validated_params["jsonCondition"] = json_condition

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
                    f"Cannot create text determinant: Service '{service_id}' "
                    "not found. Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="textdeterminant",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                determinant_data = await client.post(
                    "/service/{service_id}/textdeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": determinant_data.get("id"),
                        "name": determinant_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                return {
                    "id": determinant_data.get("id"),
                    "name": determinant_data.get("name"),
                    "type": "text",
                    "operator": determinant_data.get("operator"),
                    "target_form_field_key": determinant_data.get("targetFormFieldKey"),
                    "condition_logic": determinant_data.get("conditionLogic"),
                    "json_condition": determinant_data.get("jsonCondition"),
                    "service_id": service_id,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="determinant")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


async def textdeterminant_update(
    service_id: str | int,
    determinant_id: str | int,
    name: str | None = None,
    operator: str | None = None,
    target_form_field_key: str | None = None,
    condition_logic: str | None = None,
    json_condition: str | None = None,
) -> dict[str, Any]:
    """Update an existing text determinant.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Capture current state for rollback
    3. Create PENDING audit record with previous_state
    4. Execute PUT /service/{service_id}/textdeterminant API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        service_id: ID of the parent service (required).
        determinant_id: ID of the determinant to update (required).
        name: New name for the determinant (optional).
        operator: Comparison operator (optional). Valid values: equals, notEquals,
            contains, notContains, startsWith, endsWith, isEmpty, isNotEmpty.
        target_form_field_key: The form field key this determinant targets (optional).
        condition_logic: New condition logic (optional).
        json_condition: New JSON condition (optional).

    Returns:
        dict: Updated determinant details including:
            - id, name, type, operator, target_form_field_key
            - condition_logic, json_condition
            - service_id: The parent service ID
            - previous_state: The state before update (for rollback reference)
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, determinant not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_textdeterminant_update_params(
        service_id,
        determinant_id,
        name,
        operator,
        target_form_field_key,
        condition_logic,
        json_condition,
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
                    "/determinant/{id}",
                    path_params={"id": determinant_id},
                    resource_type="determinant",
                    resource_id=determinant_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Determinant '{determinant_id}' not found. "
                    "Use 'determinant_list' with service_id to see determinants."
                )

            # Normalize previous_state to snake_case for consistency
            normalized_previous_state = {
                "id": previous_state.get("id"),
                "name": previous_state.get("name"),
                "operator": previous_state.get("operator"),
                "target_form_field_key": previous_state.get("targetFormFieldKey"),
                "condition_logic": previous_state.get("conditionLogic"),
                "json_condition": previous_state.get("jsonCondition"),
            }

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="textdeterminant",
                object_id=str(determinant_id),
                params={
                    "service_id": str(service_id),
                    "changes": validated_params,
                },
            )

            # Save rollback state for undo capability
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="textdeterminant",
                object_id=str(determinant_id),
                previous_state={
                    "id": previous_state.get("id"),
                    "name": previous_state.get("name"),
                    "operator": previous_state.get("operator"),
                    "targetFormFieldKey": previous_state.get("targetFormFieldKey"),
                    "conditionLogic": previous_state.get("conditionLogic"),
                    "jsonCondition": previous_state.get("jsonCondition"),
                    "serviceId": service_id,
                },
            )

            try:
                determinant_data = await client.put(
                    "/service/{service_id}/textdeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                    resource_id=determinant_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": determinant_data.get("id"),
                        "name": determinant_data.get("name"),
                        "changes_applied": {
                            k: v for k, v in validated_params.items() if k != "id"
                        },
                    },
                )

                return {
                    "id": determinant_data.get("id"),
                    "name": determinant_data.get("name"),
                    "type": "text",
                    "operator": determinant_data.get("operator"),
                    "target_form_field_key": determinant_data.get("targetFormFieldKey"),
                    "condition_logic": determinant_data.get("conditionLogic"),
                    "json_condition": determinant_data.get("jsonCondition"),
                    "service_id": service_id,
                    "previous_state": normalized_previous_state,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(
                    e, resource_type="determinant", resource_id=determinant_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="determinant", resource_id=determinant_id
        )


async def selectdeterminant_create(
    service_id: str | int,
    name: str,
    operator: str,
    select_value: str,
    condition_logic: str | None = None,
    json_condition: str | None = None,
) -> dict[str, Any]:
    """Create a new select determinant within a service.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Verify parent service exists (no audit if service not found)
    3. Create PENDING audit record
    4. Execute POST /service/{service_id}/selectdeterminant API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        service_id: ID of the parent service (required).
        name: Name of the determinant (required).
        operator: Comparison operator (required). Valid values: equals, notEquals,
            contains, notContains, startsWith, endsWith, isEmpty, isNotEmpty.
        select_value: The select option value this determinant matches (required).
        condition_logic: Condition logic expression (optional).
        json_condition: JSON representation of the condition (optional).

    Returns:
        dict: Created determinant details including:
            - id: The new determinant ID
            - name, type, operator, select_value, condition_logic, json_condition
            - service_id: The parent service ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, service not found, not authenticated,
            or API error.
    """
    # Pre-flight validation
    validated_params = _validate_selectdeterminant_create_params(
        service_id, name, operator, select_value
    )

    # Add optional parameters
    if condition_logic is not None:
        validated_params["conditionLogic"] = condition_logic
    if json_condition is not None:
        validated_params["jsonCondition"] = json_condition

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
                    f"Cannot create select determinant: Service '{service_id}' "
                    "not found. Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="selectdeterminant",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                determinant_data = await client.post(
                    "/service/{service_id}/selectdeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": determinant_data.get("id"),
                        "name": determinant_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                return {
                    "id": determinant_data.get("id"),
                    "name": determinant_data.get("name"),
                    "type": "select",
                    "operator": determinant_data.get("operator"),
                    "select_value": determinant_data.get("selectValue"),
                    "condition_logic": determinant_data.get("conditionLogic"),
                    "json_condition": determinant_data.get("jsonCondition"),
                    "service_id": service_id,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="determinant")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


def register_determinant_tools(mcp: Any) -> None:
    """Register determinant tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Read operations
    mcp.tool()(determinant_list)
    mcp.tool()(determinant_get)
    # Write operations (audit-before-write pattern)
    mcp.tool()(textdeterminant_create)
    mcp.tool()(textdeterminant_update)
    mcp.tool()(selectdeterminant_create)
