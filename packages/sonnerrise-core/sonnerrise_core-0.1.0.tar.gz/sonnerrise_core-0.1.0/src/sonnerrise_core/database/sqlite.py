"""SQLite database plugin for Sonnerrise suite.

This plugin provides a lightweight SQLite backend, useful for development
and testing without requiring a full MySQL server.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event

from sonnerrise_core.database.base import DatabasePlugin


class SQLitePlugin(DatabasePlugin):
    """SQLite database plugin.

    This plugin provides SQLite connectivity for the Sonnerrise suite.
    It's primarily intended for development and testing purposes.

    When using SQLite, the 'database' config option is used as the file path.
    Use ':memory:' for an in-memory database.
    """

    def get_connection_url(self) -> str:
        """Get the SQLite connection URL.

        Returns:
            A SQLAlchemy-compatible SQLite connection URL.
        """
        db_path = self._config.database

        if db_path == ":memory:":
            return "sqlite:///:memory:"

        # Ensure the directory exists
        path = Path(db_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        path.parent.mkdir(parents=True, exist_ok=True)

        return f"sqlite:///{path}"

    def _create_engine(self) -> Engine:
        """Create and return a SQLite SQLAlchemy engine.

        Returns:
            A configured SQLAlchemy Engine instance for SQLite.
        """
        engine = create_engine(
            self.get_connection_url(),
            echo=False,
            connect_args={"check_same_thread": False},  # Allow multi-threaded access
        )

        # Enable foreign key support for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine
