"""Pytest configuration and fixtures for sonnerrise-core tests."""

import pytest

from sonnerrise_core.config import Config, DatabaseConfig


@pytest.fixture
def sqlite_config() -> Config:
    """Create a config with SQLite in-memory database."""
    return Config(
        database=DatabaseConfig(
            plugin="sqlite",
            database=":memory:",
        )
    )


@pytest.fixture
def sqlite_db(sqlite_config: Config):
    """Create an SQLite database plugin instance."""
    from sonnerrise_core.database import get_database

    db = get_database(sqlite_config)
    db.create_tables()
    yield db
    db.close()
