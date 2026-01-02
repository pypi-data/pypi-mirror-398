"""SQLite database module for audit and rollback storage.

This module provides:
- Connection management with async context manager
- Schema creation and migration system
- XDG-compliant database path handling

NFR Compliance:
- NFR5: Tamper-evident audit logs (append-only design)
- NFR11: Persist across restarts (SQLite file storage)
- NFR13: No inconsistent state (transactions)
"""

from mcp_eregistrations_bpa.db.connection import get_connection, get_db_path
from mcp_eregistrations_bpa.db.migrations import initialize_database

__all__ = [
    "get_connection",
    "get_db_path",
    "initialize_database",
]
