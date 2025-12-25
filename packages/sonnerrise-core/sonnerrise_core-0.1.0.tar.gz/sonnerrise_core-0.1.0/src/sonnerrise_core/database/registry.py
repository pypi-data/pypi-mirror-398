"""Database plugin registry for Sonnerrise suite."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sonnerrise_core.database.base import DatabasePlugin

if TYPE_CHECKING:
    from sonnerrise_core.config import Config, DatabaseConfig

# Registry of available database plugins
_plugins: dict[str, type[DatabasePlugin]] = {}


def register_plugin(name: str, plugin_class: type[DatabasePlugin]) -> None:
    """Register a database plugin.

    Args:
        name: The name to register the plugin under (e.g., "mysql", "postgresql").
        plugin_class: The plugin class to register.
    """
    _plugins[name.lower()] = plugin_class


def get_plugin_class(name: str) -> type[DatabasePlugin]:
    """Get a registered plugin class by name.

    Args:
        name: The plugin name.

    Returns:
        The plugin class.

    Raises:
        ValueError: If the plugin is not registered.
    """
    _register_builtin_plugins()
    name = name.lower()
    if name not in _plugins:
        available = ", ".join(sorted(_plugins.keys())) or "none"
        raise ValueError(f"Unknown database plugin: {name}. Available plugins: {available}")
    return _plugins[name]


def list_plugins() -> list[str]:
    """List all registered plugin names.

    Returns:
        List of registered plugin names.
    """
    _register_builtin_plugins()
    return sorted(_plugins.keys())


def get_database(config: Config | DatabaseConfig) -> DatabasePlugin:
    """Get a database plugin instance based on configuration.

    Args:
        config: Either a full Config object or just the DatabaseConfig.

    Returns:
        An initialized database plugin instance.
    """
    from sonnerrise_core.config import Config

    if isinstance(config, Config):
        db_config = config.database
    else:
        db_config = config

    plugin_class = get_plugin_class(db_config.plugin)
    return plugin_class(db_config)


def _register_builtin_plugins() -> None:
    """Register built-in database plugins."""
    if "mysql" not in _plugins:
        from sonnerrise_core.database.mysql import MySQLPlugin

        register_plugin("mysql", MySQLPlugin)

    if "sqlite" not in _plugins:
        from sonnerrise_core.database.sqlite import SQLitePlugin

        register_plugin("sqlite", SQLitePlugin)
