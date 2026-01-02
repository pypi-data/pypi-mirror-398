"""MCP server for eRegistrations BPA platform."""

import asyncio
import logging
import os
import sys
from importlib.metadata import version as get_version
from pathlib import Path

__version__ = get_version("mcp-eregistrations-bpa")

# XDG-compliant log directory
LOG_DIR = Path.home() / ".config" / "mcp-eregistrations-bpa"
LOG_FILE = LOG_DIR / "server.log"


def configure_logging() -> None:
    """Configure logging with file and stderr handlers.

    Logs are written to:
    - File: ~/.config/mcp-eregistrations-bpa/server.log (rotating, keeps last 5MB)
    - Stderr: For visibility in terminal (NOT stdout to avoid MCP stdio pollution)

    Log level is controlled by LOG_LEVEL env var (default: INFO).
    Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    from logging.handlers import RotatingFileHandler

    # Get log level from environment (default INFO)
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Create log directory if needed
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    simple_formatter = logging.Formatter("%(levelname)-8s | %(name)s | %(message)s")

    # File handler - rotating, max 5MB, keep 3 backups
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # Capture everything to file
    file_handler.setFormatter(detailed_formatter)

    # Stderr handler (NOT stdout - MCP uses stdout for JSON-RPC)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(log_level)
    stderr_handler.setFormatter(simple_formatter)

    # Configure root logger for this package
    root_logger = logging.getLogger("mcp_eregistrations_bpa")
    root_logger.setLevel(logging.DEBUG)  # Allow all levels, handlers filter
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stderr_handler)

    # Also capture httpx logs at WARNING+ level
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.WARNING)
    httpx_logger.addHandler(file_handler)


logger = logging.getLogger(__name__)


def main() -> None:
    """Run the MCP server.

    Initializes logging and SQLite database with required schema before
    starting the MCP server. Database initialization is idempotent and
    safe to run on every startup.
    """
    from mcp_eregistrations_bpa.db import initialize_database
    from mcp_eregistrations_bpa.server import mcp

    # Configure logging first
    configure_logging()

    logger.info("=" * 60)
    logger.info("MCP eRegistrations BPA Server v%s starting", __version__)
    logger.info("Log file: %s", LOG_FILE)
    logger.info("Log level: %s", os.environ.get("LOG_LEVEL", "INFO").upper())

    # Initialize database before starting server
    try:
        asyncio.run(initialize_database())
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        sys.exit(1)

    logger.info("Starting MCP server...")
    logger.info("=" * 60)
    mcp.run()
