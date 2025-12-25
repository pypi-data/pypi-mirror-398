"""Database abstraction layer for Sonnerrise suite.

Provides a plugin-based database interface for easy switching between database engines.
"""

from sonnerrise_core.database.base import DatabasePlugin, DatabaseSession
from sonnerrise_core.database.registry import get_database, register_plugin

__all__ = [
    "DatabasePlugin",
    "DatabaseSession",
    "get_database",
    "register_plugin",
]
