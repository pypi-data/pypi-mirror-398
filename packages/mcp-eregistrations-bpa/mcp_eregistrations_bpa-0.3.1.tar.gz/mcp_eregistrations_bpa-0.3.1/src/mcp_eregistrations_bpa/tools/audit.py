"""MCP tools for viewing the audit log.

This module provides tools for querying and viewing audit log entries.
Audit entries are stored locally in SQLite, tracking all write operations
performed through this MCP server.

These tools query local data only - no BPA API calls are made.
No authentication is required (the audit log is local to this MCP instance).

API Endpoints used: None (local SQLite queries only)
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.db import get_connection

__all__ = [
    "audit_list",
    "audit_get",
    "register_audit_tools",
    "VALID_OPERATION_TYPES",
    "VALID_STATUSES",
]

# Valid values for operation_type filter
VALID_OPERATION_TYPES = frozenset(["create", "update", "delete", "link", "unlink"])

# Valid values for status filter
VALID_STATUSES = frozenset(["pending", "success", "failed"])

# Maximum limit allowed
MAX_LIMIT = 100

# Default limit
DEFAULT_LIMIT = 50


def _parse_date(date_str: str) -> datetime:
    """Parse an ISO 8601 date or datetime string for validation.

    This function validates date format only. The original string is passed
    to SQLite's datetime() function for actual filtering, so timezone handling
    is delegated to SQLite.

    Supports formats:
    - YYYY-MM-DD (date only, treated as start of day)
    - YYYY-MM-DDTHH:MM:SS (datetime without timezone)
    - YYYY-MM-DDTHH:MM:SSZ (datetime with Z timezone)
    - YYYY-MM-DDTHH:MM:SS+HH:MM (datetime with offset)

    Args:
        date_str: ISO 8601 date/datetime string.

    Returns:
        Parsed datetime object (may be naive or aware depending on input).

    Raises:
        ValueError: If the format is invalid.
    """
    # Try date-only format first
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass

    # Try datetime formats
    for fmt in [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Try fromisoformat as fallback (handles more variants)
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        pass

    raise ValueError(f"Invalid date format: {date_str}")


def _validate_audit_list_params(
    from_date: str | None,
    to_date: str | None,
    operation_type: str | None,
    status: str | None,
    limit: int,
) -> dict[str, Any]:
    """Validate audit_list parameters (pre-flight).

    Args:
        from_date: Filter entries from this date.
        to_date: Filter entries up to this date.
        operation_type: Filter by operation type.
        status: Filter by status.
        limit: Maximum entries to return.

    Returns:
        Dict with validated parameters.

    Raises:
        ToolError: If validation fails.
    """
    validated: dict[str, Any] = {}

    # Validate from_date
    if from_date:
        try:
            _parse_date(from_date)
            validated["from_date"] = from_date
        except ValueError:
            raise ToolError(
                f"Invalid from_date format '{from_date}'. "
                "Use ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ."
            )

    # Validate to_date
    if to_date:
        try:
            _parse_date(to_date)
            validated["to_date"] = to_date
        except ValueError:
            raise ToolError(
                f"Invalid to_date format '{to_date}'. "
                "Use ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ."
            )

    # Validate date range order
    if from_date and to_date:
        from_dt = _parse_date(from_date)
        to_dt = _parse_date(to_date)
        if from_dt > to_dt:
            raise ToolError(
                f"from_date '{from_date}' must be before or equal to "
                f"to_date '{to_date}'."
            )

    # Validate operation_type
    if operation_type:
        if operation_type not in VALID_OPERATION_TYPES:
            raise ToolError(
                f"Invalid operation_type '{operation_type}'. "
                f"Valid types: {', '.join(sorted(VALID_OPERATION_TYPES))}."
            )
        validated["operation_type"] = operation_type

    # Validate status
    if status:
        if status not in VALID_STATUSES:
            raise ToolError(
                f"Invalid status '{status}'. "
                f"Valid statuses: {', '.join(sorted(VALID_STATUSES))}."
            )
        validated["status"] = status

    # Validate and clamp limit
    if limit <= 0:
        raise ToolError("limit must be a positive integer.")
    validated["limit"] = min(limit, MAX_LIMIT)

    return validated


def _build_audit_query(
    from_date: str | None,
    to_date: str | None,
    operation_type: str | None,
    object_type: str | None,
    status: str | None,
    limit: int,
) -> tuple[str, list[Any]]:
    """Build SQL query with filters for audit_list.

    Args:
        from_date: Filter entries from this date.
        to_date: Filter entries up to this date.
        operation_type: Filter by operation type.
        object_type: Filter by object type.
        status: Filter by status.
        limit: Maximum entries to return.

    Returns:
        Tuple of (SQL query string, list of parameters).
    """
    base_query = """
        SELECT id, timestamp, user_email, operation_type, object_type,
               object_id, status
        FROM audit_logs
    """

    conditions: list[str] = []
    params: list[Any] = []

    if from_date:
        conditions.append("timestamp >= datetime(?)")
        params.append(from_date)

    if to_date:
        # For date-only format (YYYY-MM-DD), include the entire day by using < next day.
        # For datetime format (contains "T"), use <= for exact boundary matching.
        # This means entries at exactly the specified datetime are included.
        if "T" not in to_date:
            conditions.append("timestamp < datetime(?, '+1 day')")
        else:
            conditions.append("timestamp <= datetime(?)")
        params.append(to_date)

    if operation_type:
        conditions.append("operation_type = ?")
        params.append(operation_type)

    if object_type:
        conditions.append("object_type = ?")
        params.append(object_type)

    if status:
        conditions.append("status = ?")
        params.append(status)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    return base_query, params


def _transform_audit_entry_summary(row: dict[str, Any]) -> dict[str, Any]:
    """Transform database row to summary response format.

    Args:
        row: Database row dictionary.

    Returns:
        Transformed summary with snake_case keys.
    """
    return {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "user_email": row["user_email"],
        "operation_type": row["operation_type"],
        "object_type": row["object_type"],
        "object_id": row["object_id"],
        "status": row["status"],
    }


async def audit_list(
    from_date: str | None = None,
    to_date: str | None = None,
    operation_type: str | None = None,
    object_type: str | None = None,
    status: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """List audit log entries with optional filters.

    Query the audit log to review operations performed via MCP.
    By default, returns the 50 most recent entries sorted by timestamp (newest first).

    Args:
        from_date: Filter entries from this date (ISO 8601 format).
        to_date: Filter entries up to this date (ISO 8601 format).
        operation_type: Filter by operation (create, update, delete, link, unlink).
        object_type: Filter by object type (service, registration, etc.).
        status: Filter by status (pending, success, failed).
        limit: Maximum entries to return (default 50, max 100).

    Returns:
        dict: Audit entries with total count and filters applied.
            - entries: List of audit entry summaries
            - total: Number of entries returned
            - filters_applied: Dict of filters that were applied
    """
    # Validate parameters (will raise ToolError if invalid)
    validated = _validate_audit_list_params(
        from_date, to_date, operation_type, status, limit
    )
    effective_limit = validated.get("limit", DEFAULT_LIMIT)

    # Build and execute query
    query, params = _build_audit_query(
        from_date, to_date, operation_type, object_type, status, effective_limit
    )

    async with get_connection() as conn:
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

    # Transform to response format
    entries = [_transform_audit_entry_summary(dict(row)) for row in rows]

    # Build filters_applied dict (only include non-None filters)
    filters_applied: dict[str, Any] = {}
    if from_date:
        filters_applied["from_date"] = from_date
    if to_date:
        filters_applied["to_date"] = to_date
    if operation_type:
        filters_applied["operation_type"] = operation_type
    if object_type:
        filters_applied["object_type"] = object_type
    if status:
        filters_applied["status"] = status
    if limit != DEFAULT_LIMIT:
        filters_applied["limit"] = effective_limit

    return {
        "entries": entries,
        "total": len(entries),
        "filters_applied": filters_applied,
    }


async def audit_get(audit_id: str) -> dict[str, Any]:
    """Get complete details of an audit entry.

    Retrieve the full audit record including all parameters and results.
    Use this to see exactly what was sent to BPA and what was returned.

    Args:
        audit_id: The UUID of the audit entry.

    Returns:
        dict: Complete audit details including params, result, and rollback status.
            - id: UUID of the audit entry
            - timestamp: When the operation occurred
            - user_email: Who performed the operation
            - operation_type: Type of operation (create, update, delete, link, unlink)
            - object_type: Type of object affected
            - object_id: ID of the object affected (if applicable)
            - params: Full parameters passed to the operation
            - status: Operation status (pending, success, failed)
            - result: Operation result or error details
            - rollback_available: Whether rollback is possible for this entry
    """
    if not audit_id or not audit_id.strip():
        raise ToolError(
            "Cannot get audit entry: 'audit_id' is required. "
            "Use 'audit_list' to see available entries."
        )

    async with get_connection() as conn:
        cursor = await conn.execute(
            """
            SELECT id, timestamp, user_email, operation_type, object_type,
                   object_id, params, status, result, rollback_state_id
            FROM audit_logs
            WHERE id = ?
            """,
            (audit_id.strip(),),
        )
        row = await cursor.fetchone()

    if row is None:
        raise ToolError(
            f"Audit entry '{audit_id}' not found. "
            "Use 'audit_list' to see available entries."
        )

    row_dict = dict(row)

    # Parse JSON fields
    params = json.loads(row_dict["params"]) if row_dict["params"] else {}
    result = json.loads(row_dict["result"]) if row_dict["result"] else None

    # Determine rollback availability
    # Rollback is available if: status is success AND rollback_state_id exists
    rollback_available = (
        row_dict["status"] == "success" and row_dict["rollback_state_id"] is not None
    )

    return {
        "id": row_dict["id"],
        "timestamp": row_dict["timestamp"],
        "user_email": row_dict["user_email"],
        "operation_type": row_dict["operation_type"],
        "object_type": row_dict["object_type"],
        "object_id": row_dict["object_id"],
        "params": params,
        "status": row_dict["status"],
        "result": result,
        "rollback_available": rollback_available,
    }


def register_audit_tools(mcp: Any) -> None:
    """Register audit tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(audit_list)
    mcp.tool()(audit_get)
