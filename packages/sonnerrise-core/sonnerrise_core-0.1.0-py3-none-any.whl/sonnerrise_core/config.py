"""Configuration loader for Sonnerrise suite.

Loads configuration from YAML files with support for environment variable overrides.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    plugin: str = Field(default="mysql", description="Database plugin to use")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=3306, description="Database port")
    user: str = Field(default="sonnerrise", description="Database user")
    password: str = Field(default="", description="Database password")
    database: str = Field(default="sonnerrise", description="Database name")
    charset: str = Field(default="utf8mb4", description="Character set")

    @field_validator("port", mode="before")
    @classmethod
    def parse_port(cls, v: Any) -> int:
        if isinstance(v, str):
            return int(v)
        return v


class WebConfig(BaseModel):
    """Web interface configuration."""

    host: str = Field(default="0.0.0.0", description="Web server host")
    port: int = Field(default=5000, description="Web server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    secret_key: str = Field(default="change-me-in-production", description="Flask secret key")

    @field_validator("port", mode="before")
    @classmethod
    def parse_port(cls, v: Any) -> int:
        if isinstance(v, str):
            return int(v)
        return v

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return v


class Config(BaseModel):
    """Main configuration for Sonnerrise suite."""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    web: WebConfig = Field(default_factory=WebConfig)

    @classmethod
    def from_yaml(cls, path: Path | str) -> Config:
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls.model_validate(data)

    @classmethod
    def from_env(cls) -> Config:
        """Create configuration from environment variables."""
        data: dict[str, Any] = {"database": {}, "web": {}}

        # Database settings from environment
        env_mapping = {
            "SONNERRISE_DB_PLUGIN": ("database", "plugin"),
            "SONNERRISE_DB_HOST": ("database", "host"),
            "SONNERRISE_DB_PORT": ("database", "port"),
            "SONNERRISE_DB_USER": ("database", "user"),
            "SONNERRISE_DB_PASSWORD": ("database", "password"),
            "SONNERRISE_DB_NAME": ("database", "database"),
            "SONNERRISE_DB_CHARSET": ("database", "charset"),
            "SONNERRISE_WEB_HOST": ("web", "host"),
            "SONNERRISE_WEB_PORT": ("web", "port"),
            "SONNERRISE_WEB_DEBUG": ("web", "debug"),
            "SONNERRISE_WEB_SECRET_KEY": ("web", "secret_key"),
        }

        for env_var, (section, key) in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                data[section][key] = value

        return cls.model_validate(data)

    def to_yaml(self, path: Path | str) -> None:
        """Save configuration to a YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.safe_dump(self.model_dump(), f, default_flow_style=False)


def load_config(
    path: Path | str | None = None,
    use_env: bool = True,
) -> Config:
    """Load configuration from file and/or environment.

    Args:
        path: Path to YAML configuration file. If None, uses default locations.
        use_env: Whether to override settings from environment variables.

    Returns:
        Loaded configuration object.
    """
    # Default config paths to check
    default_paths = [
        Path("sonnerrise.yaml"),
        Path("sonnerrise.yml"),
        Path("config/sonnerrise.yaml"),
        Path("config/sonnerrise.yml"),
        Path.home() / ".config" / "sonnerrise" / "config.yaml",
    ]

    config_path: Path | None = None

    if path is not None:
        config_path = Path(path)
    else:
        # Check default paths
        for default in default_paths:
            if default.exists():
                config_path = default
                break

    # Load from file or create default
    if config_path is not None and config_path.exists():
        config = Config.from_yaml(config_path)
    else:
        config = Config()

    # Override with environment variables if requested
    if use_env:
        env_config = Config.from_env()
        # Merge environment config into file config
        merged_data = config.model_dump()
        env_data = env_config.model_dump()

        for section in ("database", "web"):
            for key, value in env_data[section].items():
                # Only override if environment variable was set
                env_var = f"SONNERRISE_{'DB' if section == 'database' else 'WEB'}_{key.upper()}"
                if env_var == "SONNERRISE_DB_DATABASE":
                    env_var = "SONNERRISE_DB_NAME"
                if os.environ.get(env_var) is not None:
                    merged_data[section][key] = value

        config = Config.model_validate(merged_data)

    return config
