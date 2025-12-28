"""MCP server for eRegistrations BPA platform."""

import asyncio
import logging
import sys

__version__ = "0.1.0"

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the MCP server.

    Initializes the SQLite database with required schema before starting
    the MCP server. Database initialization is idempotent and safe to run
    on every startup.
    """
    from mcp_eregistrations_bpa.db import initialize_database
    from mcp_eregistrations_bpa.server import mcp

    # Initialize database before starting server
    try:
        asyncio.run(initialize_database())
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        sys.exit(1)

    mcp.run()
