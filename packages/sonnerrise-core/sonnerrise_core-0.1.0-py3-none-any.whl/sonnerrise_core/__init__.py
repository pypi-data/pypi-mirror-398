"""Sonnerrise Core - Configuration and database abstraction for Sonnerrise suite."""

from sonnerrise_core.config import Config, DatabaseConfig, WebConfig, load_config

# Alias for backwards compatibility and clarity
SonnerriseConfig = Config
from sonnerrise_core.database import DatabasePlugin, get_database, register_plugin
from sonnerrise_core.database.base import Base
from sonnerrise_core.models import BaseModel, TimestampMixin, import_all_models

__version__ = "0.1.0"

__all__ = [
    # Config
    "Config",
    "SonnerriseConfig",
    "DatabaseConfig",
    "WebConfig",
    "load_config",
    # Database
    "DatabasePlugin",
    "get_database",
    "register_plugin",
    # Models
    "Base",
    "BaseModel",
    "TimestampMixin",
    "import_all_models",
    # Version
    "__version__",
]
