"""Database schema creation and migration system.

Provides versioned schema migrations for audit_logs and rollback_states tables.
"""

from pathlib import Path
from typing import Any

import aiosqlite

from mcp_eregistrations_bpa.db.connection import get_connection, get_db_path

# Migration definitions: (version, sql_statements)
# Each migration is a tuple of (version_number, sql_script)
# Migrations are applied in order, only if version > current_version
MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        -- Version tracking table
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Audit logs table (NFR5: tamper-evident, append-only)
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            user_email TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            object_type TEXT NOT NULL,
            object_id TEXT,
            params TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            result TEXT,
            rollback_state_id TEXT
        );

        -- Rollback states table
        CREATE TABLE IF NOT EXISTS rollback_states (
            id TEXT PRIMARY KEY,
            audit_log_id TEXT NOT NULL REFERENCES audit_logs(id),
            object_type TEXT NOT NULL,
            object_id TEXT NOT NULL,
            previous_state TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
            ON audit_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_status
            ON audit_logs(status);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_object_type
            ON audit_logs(object_type);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_object_id
            ON audit_logs(object_id);
        CREATE INDEX IF NOT EXISTS idx_rollback_states_audit_log_id
            ON rollback_states(audit_log_id);
        CREATE INDEX IF NOT EXISTS idx_rollback_states_object
            ON rollback_states(object_type, object_id);
        """,
    ),
    (
        2,
        """
        -- Add index on user_email for filtering by user
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_email
            ON audit_logs(user_email);
        """,
    ),
    # Future migrations go here as (version, sql) tuples
]


async def get_schema_version(conn: aiosqlite.Connection) -> int:
    """Get the current schema version from the database.

    Args:
        conn: Active database connection.

    Returns:
        Current schema version number, or 0 if no version table exists.
    """
    try:
        cursor = await conn.execute("SELECT MAX(version) FROM schema_version")
        row = await cursor.fetchone()
        if row and row[0] is not None:
            version: int = row[0]
            return version
        return 0
    except aiosqlite.OperationalError:
        # Table doesn't exist yet
        return 0


async def apply_migrations(conn: aiosqlite.Connection) -> int:
    """Apply pending migrations in order.

    Args:
        conn: Active database connection.

    Returns:
        Number of migrations applied.

    Raises:
        aiosqlite.Error: If migration fails.
    """
    current_version = await get_schema_version(conn)
    migrations_applied = 0

    for version, sql in MIGRATIONS:
        if version > current_version:
            # Execute the migration script
            await conn.executescript(sql)
            # Record the applied migration
            await conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (version,),
            )
            await conn.commit()
            migrations_applied += 1

    return migrations_applied


async def initialize_database(db_path: Path | None = None) -> dict[str, Any]:
    """Initialize the database with all required tables and indexes.

    This is the main entry point for database setup. It should be called
    during MCP server startup.

    Args:
        db_path: Optional path to database. Defaults to get_db_path() if not provided.

    Returns:
        Dictionary with initialization results:
        - db_path: Path to the database file
        - schema_version: Current schema version after initialization
        - migrations_applied: Number of migrations applied
        - tables_created: List of tables in the database

    Example:
        result = await initialize_database()
        print(f"Database at {result['db_path']}")
        print(f"Schema version: {result['schema_version']}")
    """
    if db_path is None:
        db_path = get_db_path()

    async with get_connection(db_path) as conn:
        migrations_applied = await apply_migrations(conn)
        schema_version = await get_schema_version(conn)

        # Get list of tables
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        rows = await cursor.fetchall()
        tables = [row[0] for row in rows]

    return {
        "db_path": str(db_path),
        "schema_version": schema_version,
        "migrations_applied": migrations_applied,
        "tables_created": tables,
    }
