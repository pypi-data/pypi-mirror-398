"""Tests for database abstraction layer."""

from pathlib import Path

import pytest

from sonnerrise_core.config import Config, DatabaseConfig
from sonnerrise_core.database import DatabasePlugin, get_database, register_plugin
from sonnerrise_core.database.registry import get_plugin_class, list_plugins
from sonnerrise_core.database.sqlite import SQLitePlugin


class TestDatabaseRegistry:
    """Tests for database plugin registry."""

    def test_list_plugins(self):
        """Test listing available plugins."""
        plugins = list_plugins()
        assert "mysql" in plugins
        assert "sqlite" in plugins

    def test_get_plugin_class(self):
        """Test getting plugin class by name."""
        from sonnerrise_core.database.mysql import MySQLPlugin

        assert get_plugin_class("mysql") == MySQLPlugin
        assert get_plugin_class("sqlite") == SQLitePlugin

    def test_get_plugin_class_case_insensitive(self):
        """Test that plugin names are case-insensitive."""
        from sonnerrise_core.database.mysql import MySQLPlugin

        assert get_plugin_class("MySQL") == MySQLPlugin
        assert get_plugin_class("SQLITE") == SQLitePlugin

    def test_unknown_plugin(self):
        """Test that unknown plugin raises error."""
        with pytest.raises(ValueError, match="Unknown database plugin"):
            get_plugin_class("unknown")

    def test_register_custom_plugin(self):
        """Test registering a custom plugin."""

        class CustomPlugin(DatabasePlugin):
            def _create_engine(self):
                pass

            def get_connection_url(self):
                return "custom://"

        register_plugin("custom", CustomPlugin)
        assert get_plugin_class("custom") == CustomPlugin


class TestGetDatabase:
    """Tests for get_database function."""

    def test_from_config(self):
        """Test creating database from Config object."""
        config = Config(
            database=DatabaseConfig(plugin="sqlite", database=":memory:")
        )
        db = get_database(config)
        assert isinstance(db, SQLitePlugin)

    def test_from_database_config(self):
        """Test creating database from DatabaseConfig object."""
        config = DatabaseConfig(plugin="sqlite", database=":memory:")
        db = get_database(config)
        assert isinstance(db, SQLitePlugin)


class TestSQLitePlugin:
    """Tests for SQLite database plugin."""

    def test_connection_url_memory(self):
        """Test connection URL for in-memory database."""
        config = DatabaseConfig(plugin="sqlite", database=":memory:")
        db = SQLitePlugin(config)
        assert db.get_connection_url() == "sqlite:///:memory:"

    def test_connection_url_file(self, tmp_path: Path):
        """Test connection URL for file database."""
        db_path = tmp_path / "test.db"
        config = DatabaseConfig(plugin="sqlite", database=str(db_path))
        db = SQLitePlugin(config)
        url = db.get_connection_url()
        assert url.startswith("sqlite:///")
        assert "test.db" in url

    def test_engine_creation(self):
        """Test that engine is created."""
        config = DatabaseConfig(plugin="sqlite", database=":memory:")
        db = SQLitePlugin(config)
        engine = db.engine
        assert engine is not None

    def test_test_connection(self):
        """Test connection testing."""
        config = DatabaseConfig(plugin="sqlite", database=":memory:")
        db = SQLitePlugin(config)
        assert db.test_connection() is True

    def test_session_context_manager(self):
        """Test session context manager."""
        config = DatabaseConfig(plugin="sqlite", database=":memory:")
        db = SQLitePlugin(config)

        with db.session() as session:
            result = session.execute(
                __import__("sqlalchemy").text("SELECT 1")
            ).scalar()
            assert result == 1

    def test_create_tables(self):
        """Test table creation."""
        from sqlalchemy import Column, Integer, String

        from sonnerrise_core.database.base import Base

        # Define a test model
        class TestModel(Base):
            __tablename__ = "test_table"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        config = DatabaseConfig(plugin="sqlite", database=":memory:")
        db = SQLitePlugin(config)
        db.create_tables()

        # Verify table exists
        with db.session() as session:
            from sqlalchemy import text

            result = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
            ).scalar()
            assert result == "test_table"

    def test_close(self):
        """Test closing the database connection."""
        config = DatabaseConfig(plugin="sqlite", database=":memory:")
        db = SQLitePlugin(config)
        _ = db.engine  # Force engine creation
        db.close()
        assert db._engine is None


class TestMySQLPlugin:
    """Tests for MySQL database plugin."""

    def test_connection_url(self):
        """Test connection URL generation."""
        from sonnerrise_core.database.mysql import MySQLPlugin

        config = DatabaseConfig(
            plugin="mysql",
            host="localhost",
            port=3306,
            user="testuser",
            password="testpass",
            database="testdb",
        )
        db = MySQLPlugin(config)
        url = db.get_connection_url()
        assert "mysql+pymysql://" in url
        assert "testuser" in url
        assert "testpass" in url
        assert "localhost" in url
        assert "3306" in url
        assert "testdb" in url

    def test_connection_url_special_chars_password(self):
        """Test that special characters in password are URL-encoded."""
        from sonnerrise_core.database.mysql import MySQLPlugin

        config = DatabaseConfig(
            plugin="mysql",
            password="p@ss:word/test",
        )
        db = MySQLPlugin(config)
        url = db.get_connection_url()
        # Password should be URL-encoded
        assert "p%40ss%3Aword%2Ftest" in url
