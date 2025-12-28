"""Rollback manager for BPA operations.

This module provides the RollbackManager class for executing rollback operations
on BPA objects. It handles endpoint resolution, state retrieval, and API calls
to restore objects to their previous state.

Rollback strategies by operation type:
- create: DELETE the created object
- update: PUT with previous_state values to restore
- delete: POST to recreate object with previous_state
- link: Reverse the link operation (unlink)
- unlink: Reverse the unlink operation (link)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp_eregistrations_bpa.bpa_client import BPAClient
from mcp_eregistrations_bpa.bpa_client.errors import BPAClientError
from mcp_eregistrations_bpa.db import get_connection

__all__ = [
    "RollbackManager",
    "RollbackError",
    "RollbackNotPossibleError",
    "ROLLBACK_ENDPOINTS",
]


class RollbackError(Exception):
    """Base exception for rollback operations."""

    pass


class RollbackNotPossibleError(RollbackError):
    """Raised when rollback cannot be performed for a given audit entry."""

    pass


# Mapping: object_type -> (delete_endpoint, update_endpoint, create_endpoint)
# Endpoints use {id}, {service_id}, {reg_id} placeholders for substitution
ROLLBACK_ENDPOINTS: dict[str, tuple[str | None, str | None, str | None]] = {
    "service": ("/service/{id}", "/service/{id}", "/service"),
    "registration": ("/registration/{id}", "/registration/{id}", "/registration"),
    "textdeterminant": (
        None,
        "/service/{service_id}/textdeterminant",
        "/service/{service_id}/textdeterminant",
    ),
    "selectdeterminant": (
        None,
        None,
        "/service/{service_id}/selectdeterminant",
    ),
    "bot": (
        "/service/{service_id}/bot/{id}",
        "/service/{service_id}/bot/{id}",
        "/service/{service_id}/bot",
    ),
    "role": (
        "/service/{service_id}/role/{id}",
        "/service/{service_id}/role/{id}",
        "/service/{service_id}/role",
    ),
    "documentrequirement": (
        "/registration/{reg_id}/documentrequirement/{id}",
        "/registration/{reg_id}/documentrequirement/{id}",
        "/registration/{reg_id}/documentrequirement",
    ),
    "cost": (
        "/registration/{reg_id}/cost/{id}",
        "/registration/{reg_id}/cost/{id}",
        "/registration/{reg_id}/cost",
    ),
}


class RollbackManager:
    """Manages rollback operations for BPA write operations.

    This class handles:
    1. Validation of rollback eligibility
    2. Retrieval of previous state from rollback_states
    3. Endpoint resolution based on object type
    4. Execution of the rollback via BPA API
    5. Marking the original operation as rolled back
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize the RollbackManager.

        Args:
            db_path: Optional path to SQLite database. Uses default if not provided.
        """
        self._db_path = db_path

    async def _get_audit_entry(self, audit_id: str) -> dict[str, Any] | None:
        """Fetch an audit entry by ID.

        Args:
            audit_id: The UUID of the audit entry.

        Returns:
            Dict with audit entry data, or None if not found.
        """
        async with get_connection(self._db_path) as conn:
            cursor = await conn.execute(
                """
                SELECT id, timestamp, user_email, operation_type, object_type,
                       object_id, params, status, result, rollback_state_id
                FROM audit_logs
                WHERE id = ?
                """,
                (audit_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return dict(row)

    async def _get_rollback_state(
        self, rollback_state_id: str
    ) -> dict[str, Any] | None:
        """Fetch a rollback state by ID.

        Args:
            rollback_state_id: The UUID of the rollback state.

        Returns:
            Dict with rollback state data, or None if not found.
        """
        async with get_connection(self._db_path) as conn:
            cursor = await conn.execute(
                """
                SELECT id, audit_log_id, object_type, object_id,
                       previous_state, created_at
                FROM rollback_states
                WHERE id = ?
                """,
                (rollback_state_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return dict(row)

    def _check_already_rolled_back(self, result: dict[str, Any] | None) -> bool:
        """Check if an operation was already rolled back.

        Args:
            result: The result field from audit_logs (parsed JSON).

        Returns:
            True if already rolled back, False otherwise.
        """
        if result is None:
            return False
        return "rolled_back_at" in result

    async def validate_rollback(self, audit_id: str) -> dict[str, Any]:
        """Validate that a rollback can be performed for the given audit entry.

        This performs all pre-flight checks:
        1. Audit entry exists
        2. Operation status is 'success' (not failed or pending)
        3. Operation has not already been rolled back
        4. Rollback state exists

        Args:
            audit_id: The UUID of the audit entry to validate.

        Returns:
            The audit entry dict if validation passes.

        Raises:
            RollbackNotPossibleError: If rollback cannot be performed.
        """
        # Check audit entry exists
        entry = await self._get_audit_entry(audit_id)
        if entry is None:
            raise RollbackNotPossibleError(
                f"Audit entry '{audit_id}' not found. "
                "Use 'audit_list' to see available entries."
            )

        # Check status
        status = entry["status"]
        if status == "failed":
            raise RollbackNotPossibleError(
                f"Operation '{audit_id}' failed and made no changes. "
                "Nothing to rollback."
            )
        if status == "pending":
            raise RollbackNotPossibleError(
                f"Operation '{audit_id}' is still pending. "
                "Wait for it to complete before attempting rollback."
            )

        # Check if already rolled back
        result = json.loads(entry["result"]) if entry["result"] else None
        if self._check_already_rolled_back(result):
            # result is guaranteed to be a dict if check returns True
            assert result is not None
            rolled_back_at = result.get("rolled_back_at", "unknown time")
            raise RollbackNotPossibleError(
                f"Operation '{audit_id}' was already rolled back at {rolled_back_at}. "
                "Use 'audit_get' to see current state."
            )

        # Check rollback state exists
        if entry["rollback_state_id"] is None:
            raise RollbackNotPossibleError(
                f"Operation '{audit_id}' has no saved state for rollback. "
                "This may be an older operation before rollback was enabled."
            )

        return entry

    def _get_delete_endpoint(
        self, object_type: str, object_id: str, params: dict[str, Any]
    ) -> str:
        """Resolve the DELETE endpoint for an object type.

        Args:
            object_type: The type of object (service, registration, etc.)
            object_id: The ID of the object to delete.
            params: Additional parameters for endpoint resolution (service_id, etc.)

        Returns:
            The resolved DELETE endpoint path.

        Raises:
            RollbackError: If object type not supported or endpoint not available.
        """
        if object_type not in ROLLBACK_ENDPOINTS:
            raise RollbackError(
                f"Rollback not supported for object type '{object_type}'."
            )

        delete_endpoint, _, _ = ROLLBACK_ENDPOINTS[object_type]
        if delete_endpoint is None:
            raise RollbackError(
                f"DELETE operation not available for object type '{object_type}'."
            )

        # Substitute placeholders
        endpoint = delete_endpoint.replace("{id}", str(object_id))
        if "{service_id}" in endpoint:
            service_id = params.get("service_id")
            if not service_id:
                raise RollbackError(
                    f"Cannot resolve DELETE endpoint for '{object_type}': "
                    "service_id not found in params."
                )
            endpoint = endpoint.replace("{service_id}", str(service_id))
        if "{reg_id}" in endpoint:
            reg_id = params.get("registration_id") or params.get("reg_id")
            if not reg_id:
                raise RollbackError(
                    f"Cannot resolve DELETE endpoint for '{object_type}': "
                    "registration_id not found in params."
                )
            endpoint = endpoint.replace("{reg_id}", str(reg_id))

        return endpoint

    def _get_update_endpoint(
        self, object_type: str, object_id: str, params: dict[str, Any]
    ) -> str:
        """Resolve the PUT endpoint for an object type.

        Args:
            object_type: The type of object (service, registration, etc.)
            object_id: The ID of the object to update.
            params: Additional parameters for endpoint resolution.

        Returns:
            The resolved PUT endpoint path.

        Raises:
            RollbackError: If object type not supported or endpoint not available.
        """
        if object_type not in ROLLBACK_ENDPOINTS:
            raise RollbackError(
                f"Rollback not supported for object type '{object_type}'."
            )

        _, update_endpoint, _ = ROLLBACK_ENDPOINTS[object_type]
        if update_endpoint is None:
            raise RollbackError(
                f"UPDATE operation not available for object type '{object_type}'."
            )

        # Substitute placeholders
        endpoint = update_endpoint.replace("{id}", str(object_id))
        if "{service_id}" in endpoint:
            service_id = params.get("service_id")
            if not service_id:
                raise RollbackError(
                    f"Cannot resolve UPDATE endpoint for '{object_type}': "
                    "service_id not found in params."
                )
            endpoint = endpoint.replace("{service_id}", str(service_id))
        if "{reg_id}" in endpoint:
            reg_id = params.get("registration_id") or params.get("reg_id")
            if not reg_id:
                raise RollbackError(
                    f"Cannot resolve UPDATE endpoint for '{object_type}': "
                    "registration_id not found in params."
                )
            endpoint = endpoint.replace("{reg_id}", str(reg_id))

        return endpoint

    def _get_create_endpoint(self, object_type: str, params: dict[str, Any]) -> str:
        """Resolve the POST endpoint for an object type.

        Args:
            object_type: The type of object (service, registration, etc.)
            params: Additional parameters for endpoint resolution.

        Returns:
            The resolved POST endpoint path.

        Raises:
            RollbackError: If object type not supported or endpoint not available.
        """
        if object_type not in ROLLBACK_ENDPOINTS:
            raise RollbackError(
                f"Rollback not supported for object type '{object_type}'."
            )

        _, _, create_endpoint = ROLLBACK_ENDPOINTS[object_type]
        if create_endpoint is None:
            raise RollbackError(
                f"CREATE operation not available for object type '{object_type}'."
            )

        # Substitute placeholders
        endpoint = create_endpoint
        if "{service_id}" in endpoint:
            service_id = params.get("service_id")
            if not service_id:
                raise RollbackError(
                    f"Cannot resolve CREATE endpoint for '{object_type}': "
                    "service_id not found in params."
                )
            endpoint = endpoint.replace("{service_id}", str(service_id))
        if "{reg_id}" in endpoint:
            reg_id = params.get("registration_id") or params.get("reg_id")
            if not reg_id:
                raise RollbackError(
                    f"Cannot resolve CREATE endpoint for '{object_type}': "
                    "registration_id not found in params."
                )
            endpoint = endpoint.replace("{reg_id}", str(reg_id))

        return endpoint

    async def execute_rollback(
        self,
        operation_type: str,
        object_type: str,
        object_id: str,
        previous_state: dict[str, Any] | None,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the rollback operation via BPA API.

        Strategy by operation type:
        - create: DELETE the object (no previous state needed)
        - update: PUT with previous_state values
        - delete: POST to recreate with previous_state
        - link: Call unlink operation
        - unlink: Call link operation

        Args:
            operation_type: The original operation type (create, update, delete, etc.)
            object_type: The type of object.
            object_id: The ID of the object.
            previous_state: The state to restore (None for create operations).
            params: Additional context parameters from the original operation.

        Returns:
            Dict with rollback execution result.

        Raises:
            RollbackError: If the BPA API call fails.
        """
        try:
            async with BPAClient() as client:
                if operation_type == "create":
                    # Delete the created object
                    endpoint = self._get_delete_endpoint(object_type, object_id, params)
                    await client.delete(endpoint)
                    return {"action": "deleted", "object_id": object_id}

                elif operation_type == "update":
                    # Restore previous values
                    endpoint = self._get_update_endpoint(object_type, object_id, params)
                    result = await client.put(endpoint, json=previous_state)
                    return {"action": "restored", "state": result}

                elif operation_type == "delete":
                    # Recreate the object
                    endpoint = self._get_create_endpoint(object_type, params)
                    result = await client.post(endpoint, json=previous_state)
                    return {
                        "action": "recreated",
                        "new_id": result.get("id") if result else None,
                    }

                elif operation_type == "link":
                    # TODO: Implement link rollback (unlink)
                    raise RollbackError(
                        f"Rollback for '{operation_type}' operations "
                        "is not yet implemented."
                    )

                elif operation_type == "unlink":
                    # TODO: Implement unlink rollback (link)
                    raise RollbackError(
                        f"Rollback for '{operation_type}' operations "
                        "is not yet implemented."
                    )

                else:
                    raise RollbackError(
                        f"Unknown operation type '{operation_type}'. "
                        "Cannot determine rollback strategy."
                    )

        except BPAClientError as e:
            raise RollbackError(f"BPA API error during rollback: {e}")

    async def _mark_rolled_back(
        self,
        audit_id: str,
        rollback_audit_id: str,
        rolled_back_at: str,
    ) -> None:
        """Mark the original audit entry as rolled back.

        Updates the result field of the original audit entry to include
        rollback metadata, preventing double-rollback.

        Args:
            audit_id: The original audit entry ID.
            rollback_audit_id: The ID of the rollback audit entry.
            rolled_back_at: ISO 8601 timestamp of when rollback occurred.
        """
        async with get_connection(self._db_path) as conn:
            # Get current result
            cursor = await conn.execute(
                "SELECT result FROM audit_logs WHERE id = ?",
                (audit_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return

            # Update result with rollback info
            current_result = json.loads(row["result"]) if row["result"] else {}
            current_result["rolled_back_at"] = rolled_back_at
            current_result["rollback_audit_id"] = rollback_audit_id

            await conn.execute(
                "UPDATE audit_logs SET result = ? WHERE id = ?",
                (json.dumps(current_result), audit_id),
            )
            await conn.commit()

    async def perform_rollback(self, audit_id: str) -> dict[str, Any]:
        """Perform a complete rollback operation.

        This is the main entry point for rollback operations. It:
        1. Validates the rollback can be performed
        2. Retrieves the previous state
        3. Executes the rollback via BPA API
        4. Marks the original operation as rolled back

        Note: This method does NOT create an audit record for the rollback
        operation itself - that should be done by the calling tool.

        Args:
            audit_id: The UUID of the audit entry to rollback.

        Returns:
            Dict with rollback result including:
            - status: "success"
            - message: Human-readable description
            - original_operation: Details of what was rolled back
            - restored_state: The restored object state (if applicable)

        Raises:
            RollbackNotPossibleError: If validation fails.
            RollbackError: If execution fails.
        """
        # Validate rollback
        entry = await self.validate_rollback(audit_id)

        # Get rollback state
        rollback_state = await self._get_rollback_state(entry["rollback_state_id"])
        if rollback_state is None:
            raise RollbackError(
                f"Rollback state '{entry['rollback_state_id']}' not found. "
                "Database may be corrupted."
            )

        # Parse previous state
        previous_state = (
            json.loads(rollback_state["previous_state"])
            if rollback_state["previous_state"]
            else None
        )

        # Parse params for context (service_id, registration_id, etc.)
        params = json.loads(entry["params"]) if entry["params"] else {}

        # Execute rollback
        operation_type = entry["operation_type"]
        object_type = entry["object_type"]
        object_id = entry["object_id"]

        exec_result = await self.execute_rollback(
            operation_type=operation_type,
            object_type=object_type,
            object_id=object_id,
            previous_state=previous_state,
            params=params,
        )

        # Build message
        action = exec_result.get("action", "unknown")
        if action == "deleted":
            message = (
                f"Rolled back 'create' on {object_type} '{object_id}' - object deleted"
            )
        elif action == "restored":
            message = f"Rolled back 'update' on {object_type} '{object_id}'"
        elif action == "recreated":
            new_id = exec_result.get("new_id", "unknown")
            message = (
                f"Rolled back 'delete' on {object_type} '{object_id}' - "
                f"object recreated as '{new_id}'"
            )
        else:
            message = f"Rolled back '{operation_type}' on {object_type} '{object_id}'"

        # Build response
        rolled_back_at = datetime.now(UTC).isoformat()
        result: dict[str, Any] = {
            "status": "success",
            "message": message,
            "original_operation": {
                "audit_id": entry["id"],
                "operation_type": operation_type,
                "object_type": object_type,
                "object_id": object_id,
                "timestamp": entry["timestamp"],
            },
            "restored_state": previous_state,
            "rolled_back_at": rolled_back_at,
        }

        # Add new_id for recreated objects
        if action == "recreated" and exec_result.get("new_id"):
            result["new_object_id"] = exec_result["new_id"]

        return result
