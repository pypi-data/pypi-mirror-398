"""Tests for configuration discovery."""

import os
import pytest
from pathlib import Path
import tempfile
import shutil

from py_logex.config import ConfigManager
from py_logex.defaults import get_default_yaml


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def config_manager():
    """Create fresh config manager for each test."""
    return ConfigManager()


def test_discover_config_creates_default(temp_dir, config_manager, monkeypatch):
    """Test that default config is created when none exists."""
    monkeypatch.chdir(temp_dir)

    config_path = config_manager.discover_config()

    assert config_path.exists()
    assert config_path.name == "logging.yaml"
    assert "logger:" in config_path.read_text()


def test_discover_config_from_env_var(temp_dir, config_manager, monkeypatch):
    """Test config discovery from environment variable."""
    config_file = temp_dir / "custom" / "my-config.yaml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text(get_default_yaml("test"))

    monkeypatch.setenv("PYLOGEX_CONFIG", str(config_file))

    config_path = config_manager.discover_config()

    assert config_path.resolve() == config_file.resolve()


def test_discover_config_env_var_not_found(temp_dir, config_manager, monkeypatch):
    """Test error when env var points to non-existent file."""
    monkeypatch.setenv("PYLOGEX_CONFIG", "/nonexistent/config.yaml")

    with pytest.raises(FileNotFoundError):
        config_manager.discover_config()


def test_discover_config_walk_up(temp_dir, config_manager, monkeypatch):
    """Test config discovery by walking up directory tree."""
    # Create nested structure
    nested = temp_dir / "src" / "utils"
    nested.mkdir(parents=True)

    # Put config at root
    config_file = temp_dir / "logging.yaml"
    config_file.write_text(get_default_yaml("test"))

    # Change to nested directory
    monkeypatch.chdir(nested)

    config_path = config_manager.discover_config()

    assert config_path.resolve() == config_file.resolve()


def test_discover_config_common_locations(temp_dir, config_manager, monkeypatch):
    """Test config discovery from common locations."""
    monkeypatch.chdir(temp_dir)

    # Create config in config/ subdirectory
    config_dir = temp_dir / "config"
    config_dir.mkdir()
    config_file = config_dir / "logging.yaml"
    config_file.write_text(get_default_yaml("test"))

    config_path = config_manager.discover_config()

    assert config_path.resolve() == config_file.resolve()


def test_load_config(temp_dir, config_manager, monkeypatch):
    """Test loading configuration from file."""
    config_file = temp_dir / "logging.yaml"
    config_file.write_text(get_default_yaml("test"))

    config = config_manager.load_config(config_file)

    assert "logger" in config
    assert config["logger"]["level"] == "INFO"


def test_get_logger_config_default(temp_dir, config_manager, monkeypatch):
    """Test getting default logger configuration."""
    config_file = temp_dir / "logging.yaml"
    config_file.write_text(get_default_yaml("test"))

    config_manager.load_config(config_file)
    logger_config = config_manager.get_logger_config()

    assert "level" in logger_config
    assert "file" in logger_config
    assert logger_config["level"] == "INFO"


def test_config_defaults(config_manager):
    """Test configuration defaults are applied."""
    config_manager._config = {"logger": {}}

    logger_config = config_manager.get_logger_config()

    assert logger_config["level"] == "INFO"
    assert logger_config["rotation"] == "500 MB"
    assert logger_config["console"]["enabled"] is True


def test_config_path_tracking(temp_dir, config_manager):
    """Test that config path is tracked after loading."""
    config_file = temp_dir / "logging.yaml"
    config_file.write_text(get_default_yaml("test"))

    config_manager.load_config(config_file)

    assert config_manager.get_config_path() == config_file
