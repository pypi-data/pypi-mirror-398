"""MCP tools for rollback operations.

This module provides tools for rolling back write operations and viewing
rollback state history. These tools enable service designers to undo
mistakes by restoring objects to their previous state.

Tools provided:
- rollback: Rollback a write operation to restore previous state
- rollback_history: View the state change history for an object

These tools query local SQLite data and call BPA API for restoration.
Authentication is required for rollback operations that call BPA API.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.db import get_connection, get_db_path
from mcp_eregistrations_bpa.rollback.manager import (
    RollbackError,
    RollbackManager,
    RollbackNotPossibleError,
)

__all__ = [
    "rollback",
    "rollback_history",
    "register_rollback_tools",
]


async def rollback(audit_id: str) -> dict[str, Any]:
    """Rollback a write operation to restore the previous state.

    Undo a create, update, or delete operation by restoring the object
    to its state before the operation. Creates an audit record for the
    rollback itself.

    This operation:
    - For 'create' operations: DELETEs the created object
    - For 'update' operations: PUTs the previous state to restore values
    - For 'delete' operations: POSTs to recreate the deleted object

    Args:
        audit_id: The UUID of the audit entry to rollback.

    Returns:
        dict: Rollback confirmation with before/after summary.
            - status: "success"
            - message: Human-readable description
            - original_operation: Details of what was rolled back
            - restored_state: The restored object state (if applicable)
            - rollback_audit_id: UUID of the new audit entry for this rollback

    Raises:
        ToolError: If rollback is not possible (not found, already rolled back,
            failed operation, pending operation, no saved state, or API error).
    """
    # Validate audit_id
    if not audit_id or not audit_id.strip():
        raise ToolError(
            "Cannot rollback: 'audit_id' is required. "
            "Use 'audit_list' to see available entries."
        )

    audit_id = audit_id.strip()
    db_path = get_db_path()
    manager = RollbackManager(db_path=db_path)

    # Create pending audit record for the rollback operation FIRST
    rollback_audit_id = str(uuid.uuid4())
    timestamp = datetime.now(UTC).isoformat()

    try:
        # Validate rollback can be performed
        # This raises RollbackNotPossibleError if validation fails
        entry = await manager.validate_rollback(audit_id)

        # Create pending audit entry for the rollback
        async with get_connection(db_path) as conn:
            await conn.execute(
                """
                INSERT INTO audit_logs (
                    id, timestamp, user_email, operation_type, object_type,
                    object_id, params, status, result, rollback_state_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rollback_audit_id,
                    timestamp,
                    entry["user_email"],
                    "rollback",
                    entry["object_type"],
                    entry["object_id"],
                    json.dumps({"rolled_back_audit_id": audit_id}),
                    "pending",
                    None,
                    None,
                ),
            )
            await conn.commit()

        # Perform the rollback
        result = await manager.perform_rollback(audit_id)

        # Mark rollback audit as success
        async with get_connection(db_path) as conn:
            await conn.execute(
                "UPDATE audit_logs SET status = ?, result = ? WHERE id = ?",
                (
                    "success",
                    json.dumps(
                        {
                            "rolled_back_audit_id": audit_id,
                            "action": result.get("message", "rollback completed"),
                        }
                    ),
                    rollback_audit_id,
                ),
            )
            await conn.commit()

        # Mark original as rolled back
        await manager._mark_rolled_back(
            audit_id=audit_id,
            rollback_audit_id=rollback_audit_id,
            rolled_back_at=timestamp,
        )

        # Add rollback_audit_id to response
        result["rollback_audit_id"] = rollback_audit_id
        return result

    except RollbackNotPossibleError as e:
        # Validation failed - don't create failed audit entry
        # (we only create audit entries for operations that were attempted)
        # Clean up the pending audit entry if it was created
        try:
            async with get_connection(db_path) as conn:
                await conn.execute(
                    "DELETE FROM audit_logs WHERE id = ? AND status = 'pending'",
                    (rollback_audit_id,),
                )
                await conn.commit()
        except Exception:
            pass  # Best effort cleanup
        raise ToolError(str(e))

    except RollbackError as e:
        # Execution failed - mark audit as failed
        try:
            async with get_connection(db_path) as conn:
                await conn.execute(
                    "UPDATE audit_logs SET status = ?, result = ? WHERE id = ?",
                    ("failed", json.dumps({"error": str(e)}), rollback_audit_id),
                )
                await conn.commit()
        except Exception:
            pass  # Best effort
        raise ToolError(f"Rollback failed: {e}")


async def rollback_history(object_type: str, object_id: str) -> dict[str, Any]:
    """Get the rollback state history for an object.

    View all saved states for an object to understand what changes
    were made and what rollback options are available.

    Args:
        object_type: The type of object (service, registration, etc.)
        object_id: The ID of the object.

    Returns:
        dict: Chronological list of state changes with rollback metadata.
            - object_type: The object type queried
            - object_id: The object ID queried
            - states: List of state records in chronological order (oldest first)
            - total: Number of state records
    """
    # Validate inputs
    if not object_type or not object_type.strip():
        raise ToolError("Cannot get rollback history: 'object_type' is required.")

    if not object_id or not object_id.strip():
        raise ToolError("Cannot get rollback history: 'object_id' is required.")

    object_type = object_type.strip()
    object_id = object_id.strip()
    db_path = get_db_path()

    async with get_connection(db_path) as conn:
        # Join rollback_states with audit_logs to get operation context
        cursor = await conn.execute(
            """
            SELECT
                rs.id as rollback_state_id,
                rs.audit_log_id as audit_id,
                rs.previous_state,
                rs.created_at,
                al.operation_type
            FROM rollback_states rs
            LEFT JOIN audit_logs al ON rs.audit_log_id = al.id
            WHERE rs.object_type = ? AND rs.object_id = ?
            ORDER BY rs.created_at ASC
            """,
            (object_type, object_id),
        )
        rows = await cursor.fetchall()

    # Transform to response format
    states = []
    for row in rows:
        previous_state = (
            json.loads(row["previous_state"]) if row["previous_state"] else None
        )
        states.append(
            {
                "rollback_state_id": row["rollback_state_id"],
                "audit_id": row["audit_id"],
                "operation_type": row["operation_type"],
                "previous_state": previous_state,
                "created_at": row["created_at"],
            }
        )

    return {
        "object_type": object_type,
        "object_id": object_id,
        "states": states,
        "total": len(states),
    }


def register_rollback_tools(mcp: Any) -> None:
    """Register rollback tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(rollback)
    mcp.tool()(rollback_history)
