"""Tests for CLI functionality."""

import pytest
from pathlib import Path
import tempfile
import shutil

from py_logex.cli import main, cmd_config_show, cmd_config_init, cmd_config_validate
from py_logex.defaults import get_default_yaml


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


def test_cli_no_command(capsys):
    """Test CLI with no command shows help."""
    result = main([])

    assert result == 0
    captured = capsys.readouterr()
    assert "py_logex" in captured.out


def test_cli_version(capsys):
    """Test version command."""
    result = main(["version"])

    assert result == 0
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out


def test_cli_config_no_subcommand(capsys):
    """Test config command without subcommand shows help."""
    result = main(["config"])

    assert result == 0
    captured = capsys.readouterr()
    assert "config" in captured.out.lower()


def test_cli_config_init_default(temp_dir, monkeypatch, capsys):
    """Test config init creates default file."""
    monkeypatch.chdir(temp_dir)

    result = main(["config", "init"])

    assert result == 0
    assert (temp_dir / "logging.yaml").exists()

    captured = capsys.readouterr()
    assert "Created" in captured.out


def test_cli_config_init_custom_output(temp_dir, capsys):
    """Test config init with custom output path."""
    output_path = temp_dir / "custom" / "config.yaml"

    result = main(["config", "init", "-o", str(output_path)])

    assert result == 0
    assert output_path.exists()


def test_cli_config_init_custom_name(temp_dir, monkeypatch, capsys):
    """Test config init with custom script name."""
    monkeypatch.chdir(temp_dir)

    result = main(["config", "init", "-n", "myapp"])

    assert result == 0

    config_file = temp_dir / "logging.yaml"
    content = config_file.read_text()
    assert "myapp.log" in content


def test_cli_config_init_no_overwrite(temp_dir, monkeypatch, capsys):
    """Test config init doesn't overwrite without --force."""
    monkeypatch.chdir(temp_dir)

    config_file = temp_dir / "logging.yaml"
    config_file.write_text("existing content")

    result = main(["config", "init"])

    assert result == 1
    captured = capsys.readouterr()
    assert "already exists" in captured.err


def test_cli_config_init_force_overwrite(temp_dir, monkeypatch, capsys):
    """Test config init with --force overwrites existing file."""
    monkeypatch.chdir(temp_dir)

    config_file = temp_dir / "logging.yaml"
    config_file.write_text("existing content")

    result = main(["config", "init", "--force"])

    assert result == 0
    assert "existing content" not in config_file.read_text()


def test_cli_config_show(temp_dir, monkeypatch, capsys):
    """Test config show displays configuration."""
    config_file = temp_dir / "logging.yaml"
    config_file.write_text(get_default_yaml("test"))

    monkeypatch.chdir(temp_dir)

    result = main(["config", "show"])

    assert result == 0
    captured = capsys.readouterr()
    assert "logging.yaml" in captured.out
    assert "logger:" in captured.out


def test_cli_config_validate_valid(temp_dir, capsys):
    """Test validating valid configuration."""
    config_file = temp_dir / "logging.yaml"
    config_file.write_text(get_default_yaml("test"))

    result = main(["config", "validate", "-c", str(config_file)])

    assert result == 0
    captured = capsys.readouterr()
    assert "valid" in captured.out.lower()


def test_cli_config_validate_invalid_yaml(temp_dir, capsys):
    """Test validating invalid YAML."""
    config_file = temp_dir / "logging.yaml"
    config_file.write_text("invalid: yaml: syntax:")

    result = main(["config", "validate", "-c", str(config_file)])

    assert result == 1
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()


def test_cli_config_validate_empty(temp_dir, capsys):
    """Test validating empty configuration."""
    config_file = temp_dir / "logging.yaml"
    config_file.write_text("")

    result = main(["config", "validate", "-c", str(config_file)])

    assert result == 1
    captured = capsys.readouterr()
    assert "empty" in captured.err.lower()


def test_cli_config_validate_missing_sections(temp_dir, capsys):
    """Test validating config with missing required sections."""
    config_file = temp_dir / "logging.yaml"
    config_file.write_text("incomplete: config")

    result = main(["config", "validate", "-c", str(config_file)])

    assert result == 1
    captured = capsys.readouterr()
    assert "missing" in captured.err.lower()


def test_cli_config_validate_autodiscover(temp_dir, monkeypatch, capsys):
    """Test validate without -c flag uses autodiscovery."""
    monkeypatch.chdir(temp_dir)

    config_file = temp_dir / "logging.yaml"
    config_file.write_text(get_default_yaml("test"))

    result = main(["config", "validate"])

    assert result == 0
    captured = capsys.readouterr()
    assert "valid" in captured.out.lower()


class MockArgs:
    """Mock args object for testing command functions directly."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_cmd_config_show_direct(temp_dir, monkeypatch, capsys):
    """Test cmd_config_show function directly."""
    monkeypatch.chdir(temp_dir)

    config_file = temp_dir / "logging.yaml"
    config_file.write_text(get_default_yaml("test"))

    args = MockArgs()
    result = cmd_config_show(args)

    assert result == 0
    captured = capsys.readouterr()
    assert "Configuration file:" in captured.out


def test_cmd_config_init_direct(temp_dir, monkeypatch, capsys):
    """Test cmd_config_init function directly."""
    monkeypatch.chdir(temp_dir)

    args = MockArgs(output=None, name="testapp", force=False)
    result = cmd_config_init(args)

    assert result == 0
    assert (temp_dir / "logging.yaml").exists()


def test_cmd_config_validate_direct(temp_dir, capsys):
    """Test cmd_config_validate function directly."""
    config_file = temp_dir / "logging.yaml"
    config_file.write_text(get_default_yaml("test"))

    args = MockArgs(config=str(config_file))
    result = cmd_config_validate(args)

    assert result == 0
    captured = capsys.readouterr()
    assert "valid" in captured.out.lower()
