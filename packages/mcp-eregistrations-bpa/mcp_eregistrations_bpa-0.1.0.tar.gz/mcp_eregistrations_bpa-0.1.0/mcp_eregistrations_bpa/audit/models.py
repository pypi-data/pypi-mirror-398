"""Audit models for tracking BPA operations."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class AuditStatus(str, Enum):
    """Status of an audit log entry."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class OperationType(str, Enum):
    """Type of operation being audited."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LINK = "link"
    UNLINK = "unlink"


class ObjectType(str, Enum):
    """Type of object being operated on."""

    SERVICE = "service"
    REGISTRATION = "registration"
    FIELD = "field"
    DETERMINANT = "determinant"
    ACTION = "action"


@dataclass
class AuditEntry:
    """Represents a single audit log entry for a BPA operation.

    Audit entries are created BEFORE operations execute (with status='pending')
    and updated AFTER completion (with status='success' or 'failed').
    """

    id: str
    timestamp: str
    user_email: str
    operation_type: str
    object_type: str
    params: dict[str, Any]
    status: AuditStatus = AuditStatus.PENDING
    object_id: str | None = None
    result: dict[str, Any] | None = None
    rollback_state_id: str | None = None

    @classmethod
    def create(
        cls,
        user_email: str,
        operation_type: str,
        object_type: str,
        params: dict[str, Any],
        object_id: str | None = None,
    ) -> AuditEntry:
        """Factory method for creating new audit entries.

        Args:
            user_email: Email of the user performing the operation
            operation_type: Type (create, update, delete, link, unlink)
            object_type: Type (service, registration, field, determinant, action)
            params: Parameters passed to the operation
            object_id: Optional ID of the object being operated on

        Returns:
            A new AuditEntry with generated UUID and timestamp
        """
        return cls(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
            user_email=user_email,
            operation_type=operation_type,
            object_type=object_type,
            params=params,
            object_id=object_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for database storage.

        Returns:
            Dictionary with all fields, params/result serialized as JSON strings
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "user_email": self.user_email,
            "operation_type": self.operation_type,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "params": json.dumps(self.params),
            "status": self.status.value,
            "result": json.dumps(self.result) if self.result else None,
            "rollback_state_id": self.rollback_state_id,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> AuditEntry:
        """Create from database row.

        Args:
            row: Dictionary with database column values

        Returns:
            AuditEntry instance with deserialized data
        """
        return cls(
            id=row["id"],
            timestamp=row["timestamp"],
            user_email=row["user_email"],
            operation_type=row["operation_type"],
            object_type=row["object_type"],
            object_id=row["object_id"],
            params=json.loads(row["params"]),
            status=AuditStatus(row["status"]),
            result=json.loads(row["result"]) if row["result"] else None,
            rollback_state_id=row["rollback_state_id"],
        )
