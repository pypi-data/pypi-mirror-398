"""Audit logging module for tracking BPA operations.

This module provides:
- AuditLogger: Main class for recording and querying audit logs
- AuditEntry: Dataclass representing a single audit log entry
- AuditStatus: Enum for audit entry status (pending, success, failed)

Usage:
    from mcp_eregistrations_bpa.audit import AuditLogger, AuditStatus

    logger = AuditLogger()

    # Record BEFORE operation
    audit_id = await logger.record_pending(
        user_email="user@example.com",
        operation_type="create",
        object_type="registration",
        params={"name": "New Registration"},
    )

    # Execute operation, then update audit
    try:
        result = await do_operation()
        await logger.mark_success(audit_id, result)
    except Exception as e:
        await logger.mark_failed(audit_id, str(e))
        raise
"""

from mcp_eregistrations_bpa.audit.context import (
    NotAuthenticatedError,
    get_current_user_email,
)
from mcp_eregistrations_bpa.audit.logger import (
    AuditEntryImmutableError,
    AuditEntryNotFoundError,
    AuditLogger,
)
from mcp_eregistrations_bpa.audit.models import (
    AuditEntry,
    AuditStatus,
    ObjectType,
    OperationType,
)

__all__ = [
    "AuditLogger",
    "AuditEntry",
    "AuditEntryImmutableError",
    "AuditEntryNotFoundError",
    "AuditStatus",
    "ObjectType",
    "OperationType",
    "get_current_user_email",
    "NotAuthenticatedError",
]
