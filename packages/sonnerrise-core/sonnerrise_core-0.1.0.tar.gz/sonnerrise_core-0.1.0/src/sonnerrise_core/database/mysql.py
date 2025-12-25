"""MySQL database plugin for Sonnerrise suite."""

from __future__ import annotations

from urllib.parse import quote_plus

from sqlalchemy import Engine, create_engine

from sonnerrise_core.database.base import DatabasePlugin


class MySQLPlugin(DatabasePlugin):
    """MySQL database plugin using PyMySQL driver.

    This plugin provides MySQL connectivity for the Sonnerrise suite.
    It uses the PyMySQL driver which is a pure-Python MySQL client.
    """

    def get_connection_url(self) -> str:
        """Get the MySQL connection URL.

        Returns:
            A SQLAlchemy-compatible MySQL connection URL.
        """
        # URL-encode the password in case it contains special characters
        password = quote_plus(self._config.password) if self._config.password else ""

        return (
            f"mysql+pymysql://{self._config.user}:{password}"
            f"@{self._config.host}:{self._config.port}"
            f"/{self._config.database}?charset={self._config.charset}"
        )

    def _create_engine(self) -> Engine:
        """Create and return a MySQL SQLAlchemy engine.

        Returns:
            A configured SQLAlchemy Engine instance for MySQL.
        """
        return create_engine(
            self.get_connection_url(),
            pool_pre_ping=True,  # Enable connection health checks
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False,
        )
