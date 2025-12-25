"""Tests for configuration loading."""

import os
import tempfile
from pathlib import Path

import pytest

from sonnerrise_core.config import Config, DatabaseConfig, WebConfig, load_config


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_defaults(self):
        """Test default values."""
        config = DatabaseConfig()
        assert config.plugin == "mysql"
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.user == "sonnerrise"
        assert config.password == ""
        assert config.database == "sonnerrise"
        assert config.charset == "utf8mb4"

    def test_custom_values(self):
        """Test custom values."""
        config = DatabaseConfig(
            plugin="sqlite",
            host="db.example.com",
            port=3307,
            user="testuser",
            password="testpass",
            database="testdb",
        )
        assert config.plugin == "sqlite"
        assert config.host == "db.example.com"
        assert config.port == 3307
        assert config.user == "testuser"
        assert config.password == "testpass"
        assert config.database == "testdb"

    def test_port_string_conversion(self):
        """Test that port can be provided as string."""
        config = DatabaseConfig(port="3307")
        assert config.port == 3307


class TestWebConfig:
    """Tests for WebConfig."""

    def test_defaults(self):
        """Test default values."""
        config = WebConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 5000
        assert config.debug is False
        assert config.secret_key == "change-me-in-production"

    def test_debug_string_conversion(self):
        """Test that debug can be provided as string."""
        config = WebConfig(debug="true")
        assert config.debug is True

        config = WebConfig(debug="false")
        assert config.debug is False


class TestConfig:
    """Tests for main Config class."""

    def test_defaults(self):
        """Test that default config is created properly."""
        config = Config()
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.web, WebConfig)

    def test_from_yaml(self, tmp_path: Path):
        """Test loading from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
database:
  plugin: sqlite
  database: test.db
web:
  port: 8080
  debug: true
""")
        config = Config.from_yaml(config_file)
        assert config.database.plugin == "sqlite"
        assert config.database.database == "test.db"
        assert config.web.port == 8080
        assert config.web.debug is True

    def test_from_yaml_missing_file(self, tmp_path: Path):
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError):
            Config.from_yaml(tmp_path / "nonexistent.yaml")

    def test_to_yaml(self, tmp_path: Path):
        """Test saving to YAML file."""
        config = Config(
            database=DatabaseConfig(plugin="sqlite", database="test.db"),
            web=WebConfig(port=8080),
        )
        output_file = tmp_path / "output.yaml"
        config.to_yaml(output_file)

        assert output_file.exists()
        loaded = Config.from_yaml(output_file)
        assert loaded.database.plugin == "sqlite"
        assert loaded.database.database == "test.db"
        assert loaded.web.port == 8080

    def test_from_env(self, monkeypatch):
        """Test loading from environment variables."""
        monkeypatch.setenv("SONNERRISE_DB_PLUGIN", "sqlite")
        monkeypatch.setenv("SONNERRISE_DB_HOST", "testhost")
        monkeypatch.setenv("SONNERRISE_DB_PORT", "3307")
        monkeypatch.setenv("SONNERRISE_WEB_PORT", "8080")
        monkeypatch.setenv("SONNERRISE_WEB_DEBUG", "true")

        config = Config.from_env()
        assert config.database.plugin == "sqlite"
        assert config.database.host == "testhost"
        assert config.database.port == 3307
        assert config.web.port == 8080
        assert config.web.debug is True


class TestLoadConfig:
    """Tests for load_config function."""

    def test_default_config(self, monkeypatch):
        """Test loading default config when no file exists."""
        # Clear any env vars
        for key in list(os.environ.keys()):
            if key.startswith("SONNERRISE_"):
                monkeypatch.delenv(key, raising=False)

        config = load_config()
        assert isinstance(config, Config)

    def test_load_from_file(self, tmp_path: Path, monkeypatch):
        """Test loading from specific file."""
        config_file = tmp_path / "test-config.yaml"
        config_file.write_text("""
database:
  plugin: sqlite
  database: ":memory:"
""")
        config = load_config(config_file)
        assert config.database.plugin == "sqlite"
        assert config.database.database == ":memory:"

    def test_env_override(self, tmp_path: Path, monkeypatch):
        """Test that environment variables override file settings."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
database:
  plugin: mysql
  host: filehost
""")
        monkeypatch.setenv("SONNERRISE_DB_HOST", "envhost")

        config = load_config(config_file, use_env=True)
        assert config.database.plugin == "mysql"  # From file
        assert config.database.host == "envhost"  # From env

    def test_disable_env_override(self, tmp_path: Path, monkeypatch):
        """Test disabling environment variable override."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
database:
  host: filehost
""")
        monkeypatch.setenv("SONNERRISE_DB_HOST", "envhost")

        config = load_config(config_file, use_env=False)
        assert config.database.host == "filehost"
