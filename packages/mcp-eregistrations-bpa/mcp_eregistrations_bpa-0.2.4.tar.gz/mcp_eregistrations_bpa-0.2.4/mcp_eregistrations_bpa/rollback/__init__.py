"""Rollback capability module.

This module provides rollback functionality for BPA write operations,
allowing users to undo changes by restoring objects to their previous state.
"""

from mcp_eregistrations_bpa.rollback.manager import (
    ROLLBACK_ENDPOINTS,
    RollbackError,
    RollbackManager,
    RollbackNotPossibleError,
)

__all__ = [
    "RollbackManager",
    "RollbackError",
    "RollbackNotPossibleError",
    "ROLLBACK_ENDPOINTS",
]
