"""Tests for logger functionality."""

import sys
import pytest
from pathlib import Path
import tempfile
import shutil
import time

from py_logex import logger, get_logger
from py_logex.defaults import get_default_yaml


@pytest.fixture(autouse=True)
def reset_loggers():
    """Reset logger singletons between tests."""
    import py_logex.logger
    import py_logex.config
    from loguru import logger as loguru_logger

    # BEFORE test: Clean slate
    try:
        loguru_logger.remove()
    except ValueError:
        pass

    py_logex.logger._default_logger = None
    py_logex.logger._configured = False
    py_logex.config._config_manager = py_logex.config.ConfigManager()

    yield

    # AFTER test: Force cleanup
    try:
        loguru_logger.remove()
    except ValueError:
        pass

    # Force flush any pending writes
    sys.stdout.flush()
    sys.stderr.flush()

    py_logex.logger._default_logger = None
    py_logex.logger._configured = False
    py_logex.config._config_manager = py_logex.config.ConfigManager()


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration file."""
    config_file = temp_dir / "logging.yaml"
    config_content = """
logger:
  file: test.log
  level: DEBUG
  rotation: 10 MB
  retention: 1 days
  format: "{time} | {level} | {message}"
  console:
    enabled: false
"""
    config_file.write_text(config_content)
    return config_file


def test_default_logger_import():
    """Test that default logger can be imported."""
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "debug")
    assert hasattr(logger, "error")


def test_logger_basic_logging(temp_dir, test_config, monkeypatch):
    """Test basic logging functionality."""
    monkeypatch.chdir(temp_dir)

    test_logger = get_logger(config_path=test_config)

    test_logger.info("Test info message")
    test_logger.debug("Test debug message")
    test_logger.warning("Test warning message")

    test_logger.complete()
    time.sleep(0.1)

    log_file = temp_dir / "test.log"
    assert log_file.exists()

    log_content = log_file.read_text()
    assert "Test info message" in log_content
    assert "Test debug message" in log_content


def test_logger_singleton(test_config):
    """Test that logger follows singleton pattern."""
    logger1 = get_logger(config_path=test_config)
    logger2 = get_logger(config_path=test_config)

    assert logger1 is logger2


def test_logger_exception_handling(temp_dir, test_config, monkeypatch):
    """Test exception logging."""
    monkeypatch.chdir(temp_dir)

    test_logger = get_logger(config_path=test_config)

    try:
        raise ValueError("Test exception")
    except Exception as e:
        test_logger.exception(e)

    test_logger.complete()
    time.sleep(0.1)

    log_file = temp_dir / "test.log"
    log_content = log_file.read_text()

    assert "ValueError" in log_content
    assert "Test exception" in log_content
    assert "Traceback" in log_content


def test_logger_all_levels(temp_dir, test_config, monkeypatch):
    """Test all logging levels."""
    monkeypatch.chdir(temp_dir)

    test_logger = get_logger(config_path=test_config)

    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.success("Success message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
    test_logger.critical("Critical message")

    test_logger.complete()
    time.sleep(0.2)

    log_file = temp_dir / "test.log"
    assert log_file.exists()


def test_logger_reconfigure(temp_dir, test_config, monkeypatch):
    """Test reconfiguring logger."""
    monkeypatch.chdir(temp_dir)

    test_logger = get_logger(config_path=test_config)
    test_logger.info("Before reconfigure")

    # Create new config
    new_config = temp_dir / "new_logging.yaml"
    new_config.write_text("""
    logger:
      file: new_test.log
      level: ERROR
      console:
        enabled: false
    """)
    test_logger.set_config(new_config)
    test_logger.error("After reconfigure")

    test_logger.complete()
    time.sleep(0.1)

    assert (temp_dir / "new_test.log").exists()


def test_logger_context_binding(temp_dir, test_config, monkeypatch):
    """Test logger context binding."""
    monkeypatch.chdir(temp_dir)

    test_logger = get_logger(config_path=test_config)

    bound_logger = test_logger.bind(user_id=123, request_id="abc")
    bound_logger.info("User action")

    bound_logger.complete()
    time.sleep(0.1)

    log_file = temp_dir / "test.log"
    assert log_file.exists()


def test_logger_catch_decorator(temp_dir, test_config, monkeypatch):
    """Test logger catch decorator."""
    monkeypatch.chdir(temp_dir)

    test_logger = get_logger(config_path=test_config)

    @test_logger.catch
    def risky_function():
        raise RuntimeError("Something went wrong")

    # Should catch and log exception
    risky_function()

    test_logger.complete()
    time.sleep(0.1)

    log_file = temp_dir / "test.log"
    log_content = log_file.read_text()
    assert "RuntimeError" in log_content


def test_console_disabled(temp_dir, test_config, monkeypatch, capsys):
    """Test that console output can be disabled."""
    monkeypatch.chdir(temp_dir)

    test_logger = get_logger(config_path=test_config)
    test_logger.info("This should not appear in console")

    test_logger.complete()
    time.sleep(0.1)

    captured = capsys.readouterr()
    # Console is disabled in test_config
    assert "This should not appear in console" not in captured.out
