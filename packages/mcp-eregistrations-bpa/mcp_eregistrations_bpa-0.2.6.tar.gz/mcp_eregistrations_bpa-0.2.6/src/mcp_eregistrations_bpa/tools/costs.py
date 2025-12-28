"""MCP tools for BPA cost operations.

This module provides tools for creating, updating, and deleting BPA costs.
Costs define fees that applicants must pay for a registration.
Two cost types are supported: fixed costs and formula-based costs.

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED

API Endpoints used:
- POST /registration/{registration_id}/fixcost - Create fixed cost
- POST /registration/{registration_id}/formulacost - Create formula cost
- PUT /cost - Update cost
- DELETE /cost/{cost_id} - Delete cost
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
    "cost_create_fixed",
    "cost_create_formula",
    "cost_update",
    "cost_delete",
    "register_cost_tools",
]


def _transform_cost_response(
    data: dict[str, Any], cost_type: str | None = None
) -> dict[str, Any]:
    """Transform cost API response from camelCase to snake_case.

    Args:
        data: Raw API response with camelCase keys.
        cost_type: Optional cost type override ("fixed" or "formula").

    Returns:
        dict: Transformed response with snake_case keys.
    """
    result: dict[str, Any] = {
        "id": data.get("id"),
        "name": data.get("name"),
        "description": data.get("additionalInformation") or data.get("description"),
        "cost_type": cost_type or data.get("costType") or data.get("type"),
        "registration_id": data.get("registrationId"),
    }

    # Include type-specific fields (API uses fixValue, currencyId)
    if data.get("fixValue") is not None:
        result["amount"] = data.get("fixValue")
    elif data.get("amount") is not None:
        result["amount"] = data.get("amount")
    if data.get("formula"):
        result["formula"] = data.get("formula")
    if data.get("currencyId"):
        result["currency"] = data.get("currencyId")
    elif data.get("currency"):
        result["currency"] = data.get("currency")
    if data.get("variables"):
        result["variables"] = data.get("variables")

    return result


def _validate_cost_create_fixed_params(
    registration_id: str | int,
    name: str,
    amount: float,
    currency: str,
    description: str | None,
) -> dict[str, Any]:
    """Validate cost_create_fixed parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        registration_id: Parent registration ID (required).
        name: Cost name (required).
        amount: Cost amount (required, must be >= 0).
        currency: Currency code (required).
        description: Cost description (optional).

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

    if amount is None:
        errors.append("'amount' is required")
    elif amount < 0:
        errors.append("'amount' must be a non-negative number")

    # Note: currency parameter is accepted but currently ignored
    # BPA API expects currencyId as a database UUID, not ISO code

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot create fixed cost: {error_msg}.")

    # API uses fixValue (not amount), costType discriminator
    # Note: currencyId expects a database UUID, not ISO code - omit for now
    params: dict[str, Any] = {
        "name": name.strip(),
        "fixValue": amount,
        "costType": "FIX",
    }
    if description:
        params["additionalInformation"] = description.strip()

    return params


async def cost_create_fixed(
    registration_id: str | int,
    name: str,
    amount: float,
    currency: str = "USD",
    description: str | None = None,
) -> dict[str, Any]:
    """Create a fixed cost for a BPA registration.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Verify parent registration exists (no audit if not found)
    3. Create PENDING audit record
    4. Execute POST /registration/{registration_id}/fixcost API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        registration_id: ID of the parent registration (required).
        name: Name of the cost (required).
        amount: Fixed amount for the cost (required, must be >= 0).
        currency: Currency code (default: "USD").
        description: Description of the cost (optional).

    Returns:
        dict: Created cost details including:
            - id: The new cost ID
            - name, description, amount, currency
            - cost_type: "fixed"
            - registration_id: The parent registration ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, registration not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_cost_create_fixed_params(
        registration_id, name, amount, currency, description
    )

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
                    f"Cannot create fixed cost: Registration '{registration_id}' "
                    "not found. Use 'registration_list' to see available registrations."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="cost",
                params={
                    "registration_id": str(registration_id),
                    "cost_type": "fixed",
                    **validated_params,
                },
            )

            try:
                cost_data = await client.post(
                    "/registration/{registration_id}/fixcost",
                    path_params={"registration_id": registration_id},
                    json=validated_params,
                    resource_type="cost",
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "cost_id": cost_data.get("id"),
                        "name": cost_data.get("name"),
                        "amount": validated_params["fixValue"],
                        "registration_id": str(registration_id),
                    },
                )

                result = _transform_cost_response(cost_data, cost_type="fixed")
                # Explicitly set registration_id from function parameter
                result["registration_id"] = registration_id
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="cost")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="registration", resource_id=registration_id
        )


def _validate_cost_create_formula_params(
    registration_id: str | int,
    name: str,
    formula: str,
    variables: dict[str, Any] | None,
    description: str | None,
) -> dict[str, Any]:
    """Validate cost_create_formula parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        registration_id: Parent registration ID (required).
        name: Cost name (required).
        formula: Cost formula expression (required).
        variables: Variable definitions for formula (optional).
        description: Cost description (optional).

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

    if not formula or not formula.strip():
        errors.append("'formula' is required and cannot be empty")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create formula cost: {error_msg}. Check required fields."
        )

    # API expects formulaCostItems array with infixFormula, plus costType discriminator
    params: dict[str, Any] = {
        "name": name.strip(),
        "costType": "FORMULA",
        "formulaCostItems": [
            {
                "infixFormula": formula.strip(),
                "sortOrder": 0,
            }
        ],
    }
    if description:
        params["additionalInformation"] = description.strip()
    # Note: variables parameter is currently not used by API

    return params


async def cost_create_formula(
    registration_id: str | int,
    name: str,
    formula: str,
    variables: dict[str, Any] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Create a formula-based cost for a BPA registration.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Verify parent registration exists (no audit if not found)
    3. Create PENDING audit record
    4. Execute POST /registration/{registration_id}/formulacost API call
    5. Update audit record to SUCCESS or FAILED

    Args:
        registration_id: ID of the parent registration (required).
        name: Name of the cost (required).
        formula: Formula expression for calculating the cost (required).
        variables: Variable definitions used in the formula (optional).
        description: Description of the cost (optional).

    Returns:
        dict: Created cost details including:
            - id: The new cost ID
            - name, description, formula, variables
            - cost_type: "formula"
            - registration_id: The parent registration ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, registration not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_cost_create_formula_params(
        registration_id, name, formula, variables, description
    )

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
                    f"Cannot create formula cost: Registration '{registration_id}' "
                    "not found. Use 'registration_list' to see available registrations."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="cost",
                params={
                    "registration_id": str(registration_id),
                    "cost_type": "formula",
                    **validated_params,
                },
            )

            try:
                cost_data = await client.post(
                    "/registration/{registration_id}/formulacost",
                    path_params={"registration_id": registration_id},
                    json=validated_params,
                    resource_type="cost",
                )

                # Mark audit as success
                formula_str = validated_params["formulaCostItems"][0]["infixFormula"]
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "cost_id": cost_data.get("id"),
                        "name": cost_data.get("name"),
                        "formula": formula_str,
                        "registration_id": str(registration_id),
                    },
                )

                result = _transform_cost_response(cost_data, cost_type="formula")
                # Explicitly set registration_id from function parameter
                result["registration_id"] = registration_id
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="cost")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="registration", resource_id=registration_id
        )


def _validate_cost_update_params(
    cost_id: str | int,
    name: str | None,
    amount: float | None,
    formula: str | None,
    description: str | None,
) -> dict[str, Any]:
    """Validate cost_update parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.

    Args:
        cost_id: ID of cost to update (required).
        name: New name (optional).
        amount: New amount for fixed costs (optional).
        formula: New formula for formula costs (optional).
        description: New description (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not cost_id:
        errors.append("'cost_id' is required")

    if name is not None and not name.strip():
        errors.append("'name' cannot be empty when provided")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if amount is not None and amount < 0:
        errors.append("'amount' must be a non-negative number when provided")

    if formula is not None and not formula.strip():
        errors.append("'formula' cannot be empty when provided")

    # At least one field must be provided for update
    if name is None and amount is None and formula is None and description is None:
        errors.append(
            "At least one field (name, amount, formula, description) must be provided"
        )

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot update cost: {error_msg}. Check required fields.")

    params: dict[str, Any] = {"id": cost_id}
    if name is not None:
        params["name"] = name.strip()
    if amount is not None:
        params["amount"] = amount
    if formula is not None:
        params["formula"] = formula.strip()
    if description is not None:
        params["description"] = description.strip()

    return params


async def cost_update(
    cost_id: str | int,
    name: str | None = None,
    amount: float | None = None,
    formula: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Update an existing BPA cost.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Create PENDING audit record
    3. Execute PUT /cost API call
    4. Update audit record to SUCCESS or FAILED

    Note: Due to API limitations (no GET /cost/{id}),
    previous state cannot be captured for rollback.

    Args:
        cost_id: ID of the cost to update (required).
        name: New name for the cost (optional).
        amount: New amount for fixed costs (optional).
        formula: New formula for formula costs (optional).
        description: New description for the cost (optional).

    Returns:
        dict: Updated cost details including:
            - id, name, description, cost_type
            - amount or formula (depending on type)
            - registration_id: The parent registration ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, cost not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_cost_update_params(
        cost_id, name, amount, formula, description
    )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Create audit record BEFORE API call (audit-before-write pattern)
            # Note: Cannot capture previous state - no GET endpoint for cost
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="cost",
                object_id=str(cost_id),
                params={
                    "changes": {k: v for k, v in validated_params.items() if k != "id"},
                },
            )

            try:
                cost_data = await client.put(
                    "/cost",
                    json=validated_params,
                    resource_type="cost",
                    resource_id=cost_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "cost_id": cost_data.get("id"),
                        "name": cost_data.get("name"),
                        "changes_applied": {
                            k: v for k, v in validated_params.items() if k != "id"
                        },
                    },
                )

                result = _transform_cost_response(cost_data)
                result["audit_id"] = audit_id
                return result

            except BPANotFoundError:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, f"Cost '{cost_id}' not found")
                raise ToolError(
                    f"Cost '{cost_id}' not found. "
                    "Verify the cost_id from 'cost_create_fixed' or "
                    "'cost_create_formula' response."
                )
            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="cost", resource_id=cost_id)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="cost", resource_id=cost_id)


def _validate_cost_delete_params(cost_id: str | int) -> None:
    """Validate cost_delete parameters (pre-flight).

    Raises ToolError if validation fails.

    Args:
        cost_id: Cost ID to delete (required).

    Raises:
        ToolError: If validation fails.
    """
    if not cost_id:
        raise ToolError(
            "Cannot delete cost: 'cost_id' is required. "
            "Cost IDs are returned from 'cost_create_fixed' or "
            "'cost_create_formula'."
        )


async def cost_delete(cost_id: str | int) -> dict[str, Any]:
    """Delete a BPA cost.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Create PENDING audit record
    3. Execute DELETE /cost/{cost_id} API call
    4. Update audit record to SUCCESS or FAILED

    Note: Due to API limitations (no GET /cost/{id}),
    previous state cannot be captured for rollback.

    Args:
        cost_id: ID of the cost to delete (required).

    Returns:
        dict: Deletion confirmation including:
            - deleted: True
            - cost_id: The deleted cost ID
            - audit_id: The audit record ID

    Raises:
        ToolError: If validation fails, cost not found, not authenticated,
            or API error.
    """
    # Pre-flight validation (no audit record for validation failures)
    _validate_cost_delete_params(cost_id)

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Create audit record BEFORE API call (audit-before-write pattern)
            # Note: Cannot capture previous state - no GET endpoint for cost
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="delete",
                object_type="cost",
                object_id=str(cost_id),
                params={},
            )

            try:
                await client.delete(
                    "/cost/{cost_id}",
                    path_params={"cost_id": cost_id},
                    resource_type="cost",
                    resource_id=cost_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "deleted": True,
                        "cost_id": str(cost_id),
                    },
                )

                return {
                    "deleted": True,
                    "cost_id": str(cost_id),
                    "audit_id": audit_id,
                }

            except BPANotFoundError:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, f"Cost '{cost_id}' not found")
                raise ToolError(
                    f"Cost '{cost_id}' not found. "
                    "Verify the cost_id from 'cost_create_fixed' or "
                    "'cost_create_formula' response."
                )
            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="cost", resource_id=cost_id)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="cost", resource_id=cost_id)


def register_cost_tools(mcp: Any) -> None:
    """Register cost tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Write operations (audit-before-write pattern)
    mcp.tool()(cost_create_fixed)
    mcp.tool()(cost_create_formula)
    mcp.tool()(cost_update)
    mcp.tool()(cost_delete)
