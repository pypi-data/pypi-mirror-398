"""Audit logger for tracking BPA operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp_eregistrations_bpa.audit.models import AuditEntry, AuditStatus
from mcp_eregistrations_bpa.db import get_connection


class AuditEntryNotFoundError(Exception):
    """Raised when an audit entry is not found."""

    pass


class AuditEntryImmutableError(Exception):
    """Raised when attempting to modify a finalized audit entry."""

    pass


class AuditLogger:
    """Append-only audit logger for BPA operations.

    This logger implements the audit-before-write pattern:
    1. Call record_pending() BEFORE executing the BPA operation
    2. Call mark_success() or mark_failed() AFTER the operation completes

    The audit log is append-only (NFR5): entries can only be created and
    their status updated, never deleted or modified otherwise.
    """

    def __init__(self, db_path: Path | None = None):
        """Initialize the audit logger.

        Args:
            db_path: Optional path to SQLite database. If None, uses default.
        """
        self._db_path = db_path

    async def record_pending(
        self,
        user_email: str,
        operation_type: str,
        object_type: str,
        params: dict[str, Any],
        object_id: str | None = None,
    ) -> str:
        """Record a pending operation BEFORE execution.

        This method MUST be called before executing any BPA write operation.
        It creates an audit entry with status='pending' that will be updated
        after the operation completes.

        Args:
            user_email: Email of the user performing the operation
            operation_type: Type (create, update, delete, link, unlink)
            object_type: Type (service, registration, field, determinant, action)
            params: Parameters passed to the operation
            object_id: Optional ID of the object being operated on

        Returns:
            The audit entry ID (UUID string) for use with mark_success/mark_failed
        """
        entry = AuditEntry.create(
            user_email=user_email,
            operation_type=operation_type,
            object_type=object_type,
            params=params,
            object_id=object_id,
        )

        async with get_connection(self._db_path) as conn:
            await conn.execute(
                """
                INSERT INTO audit_logs (
                    id, timestamp, user_email, operation_type, object_type,
                    object_id, params, status, result, rollback_state_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.id,
                    entry.timestamp,
                    entry.user_email,
                    entry.operation_type,
                    entry.object_type,
                    entry.object_id,
                    json.dumps(entry.params),
                    entry.status.value,
                    None,
                    None,
                ),
            )
            await conn.commit()

        return entry.id

    async def mark_success(self, audit_id: str, result: dict[str, Any]) -> None:
        """Mark operation as successful with result summary.

        Args:
            audit_id: The audit entry ID returned by record_pending()
            result: Summary of the operation result (e.g., created object ID)

        Raises:
            AuditEntryNotFoundError: If audit_id does not exist.
            AuditEntryImmutableError: If entry is not in PENDING status.
        """
        async with get_connection(self._db_path) as conn:
            # Check current status (append-only enforcement)
            cursor = await conn.execute(
                "SELECT status FROM audit_logs WHERE id = ?",
                (audit_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                raise AuditEntryNotFoundError(f"Audit entry '{audit_id}' not found")
            if row["status"] != AuditStatus.PENDING.value:
                raise AuditEntryImmutableError(
                    f"Cannot modify audit entry with status '{row['status']}'. "
                    "Only PENDING entries can be updated."
                )

            await conn.execute(
                "UPDATE audit_logs SET status = ?, result = ? WHERE id = ?",
                (AuditStatus.SUCCESS.value, json.dumps(result), audit_id),
            )
            await conn.commit()

    async def mark_failed(self, audit_id: str, error_message: str) -> None:
        """Mark operation as failed with error details.

        Args:
            audit_id: The audit entry ID returned by record_pending()
            error_message: Description of the error that occurred

        Raises:
            AuditEntryNotFoundError: If audit_id does not exist.
            AuditEntryImmutableError: If entry is not in PENDING status.
        """
        async with get_connection(self._db_path) as conn:
            # Check current status (append-only enforcement)
            cursor = await conn.execute(
                "SELECT status FROM audit_logs WHERE id = ?",
                (audit_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                raise AuditEntryNotFoundError(f"Audit entry '{audit_id}' not found")
            if row["status"] != AuditStatus.PENDING.value:
                raise AuditEntryImmutableError(
                    f"Cannot modify audit entry with status '{row['status']}'. "
                    "Only PENDING entries can be updated."
                )

            await conn.execute(
                "UPDATE audit_logs SET status = ?, result = ? WHERE id = ?",
                (
                    AuditStatus.FAILED.value,
                    json.dumps({"error": error_message}),
                    audit_id,
                ),
            )
            await conn.commit()

    async def save_rollback_state(
        self,
        audit_id: str,
        object_type: str,
        object_id: str,
        previous_state: dict[str, Any],
    ) -> str:
        """Save rollback state for an audit entry.

        This enables rollback capability for update/delete operations by
        storing the previous state of the object before changes were made.

        Args:
            audit_id: The audit entry ID to associate the rollback state with.
            object_type: Type of object (service, registration, etc.).
            object_id: ID of the object.
            previous_state: The object state before the operation.

        Returns:
            The rollback state ID (UUID string).
        """
        import uuid

        rollback_state_id = str(uuid.uuid4())

        async with get_connection(self._db_path) as conn:
            # Insert rollback state
            await conn.execute(
                """
                INSERT INTO rollback_states (
                    id, audit_log_id, object_type, object_id, previous_state
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    rollback_state_id,
                    audit_id,
                    object_type,
                    object_id,
                    json.dumps(previous_state),
                ),
            )
            # Update audit entry with rollback_state_id
            await conn.execute(
                "UPDATE audit_logs SET rollback_state_id = ? WHERE id = ?",
                (rollback_state_id, audit_id),
            )
            await conn.commit()

        return rollback_state_id

    async def get_entry(self, audit_id: str) -> AuditEntry | None:
        """Retrieve audit entry by ID.

        Args:
            audit_id: The audit entry ID to retrieve

        Returns:
            The AuditEntry if found, None otherwise
        """
        async with get_connection(self._db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM audit_logs WHERE id = ?",
                (audit_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return AuditEntry.from_row(dict(row))
