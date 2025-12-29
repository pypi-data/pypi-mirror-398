"""Logger implementation for py_logex."""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger as _loguru_logger

from .config import get_config_manager
from .exceptions import format_exception_for_logging
from .utils import ensure_directory_exists

# Global state
_configured = False


def _configure_logger():
    """Configure the global loguru logger once."""
    global _configured

    if _configured:
        return

    # Remove loguru's default handler
    try:
        _loguru_logger.remove()
    except ValueError:
        pass

    # Get config
    config_manager = get_config_manager()
    config = config_manager.get_logger_config()

    # Setup file output
    log_file = config.get("file", "app.log")
    log_path = Path(log_file)

    # Always resolve to absolute path from current directory
    if not log_path.is_absolute():
        log_path = Path.cwd() / log_path

    log_path = log_path.resolve()

    ensure_directory_exists(log_path)

    # Add file handler
    _loguru_logger.add(
        sink=str(log_path),
        format=config.get("format"),
        level=config.get("level"),
        rotation=config.get("rotation"),
        retention=config.get("retention"),
        compression=config.get("compression"),
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    # Setup console output if enabled
    console_config = config.get("console", {})
    if console_config.get("enabled", True):
        _loguru_logger.add(
            sink=lambda msg: print(msg, end=""),
            format=config.get("format", "{message}"),
            level=console_config.get("level", config.get("level", "INFO")),
            colorize=console_config.get("colorize", True),
        )

    _configured = True


class PyLogexLogger:
    """Wrapper around loguru logger."""

    def __init__(self, config_path: Optional[Path] = None):
        self._logger = _loguru_logger

        if config_path:
            get_config_manager().load_config(config_path)

    def trace(self, message: str, *args, **kwargs) -> None:
        _configure_logger()
        self._logger.trace(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> None:
        _configure_logger()
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        _configure_logger()
        self._logger.info(message, *args, **kwargs)

    def success(self, message: str, *args, **kwargs) -> None:
        _configure_logger()
        self._logger.success(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        _configure_logger()
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        _configure_logger()
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        _configure_logger()
        self._logger.critical(message, *args, **kwargs)

    def exception(
        self,
        exc: Exception,
        level: str = "ERROR",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        _configure_logger()
        formatted = format_exception_for_logging(exc, level, context)

        if level.upper() == "DEBUG":
            self._logger.debug(formatted)
        elif level.upper() == "INFO":
            self._logger.info(formatted)
        elif level.upper() == "WARNING":
            self._logger.warning(formatted)
        elif level.upper() == "CRITICAL":
            self._logger.critical(formatted)
        else:
            self._logger.error(formatted)

    def log(self, level: str, message: str, *args, **kwargs) -> None:
        _configure_logger()
        self._logger.log(level, message, *args, **kwargs)

    def bind(self, **kwargs):
        _configure_logger()
        return self._logger.bind(**kwargs)

    def opt(self, **kwargs):
        _configure_logger()
        return self._logger.opt(**kwargs)

    def catch(self, *args, **kwargs):
        _configure_logger()
        return self._logger.catch(*args, **kwargs)

    def complete(self) -> None:
        self._logger.complete()
        sys.stderr.flush()
        sys.stdout.flush()

    def set_config(self, config_path: Path) -> None:
        """Reconfigure with new config."""
        global _configured
        _configured = False
        get_config_manager().load_config(config_path)
        _configure_logger()

    def remove(self, handler_id=None) -> None:
        self._logger.remove(handler_id)

    def add(self, *args, **kwargs):
        return self._logger.add(*args, **kwargs)

    def level(self, *args, **kwargs):
        return self._logger.level(*args, **kwargs)

    def disable(self, name: str) -> None:
        self._logger.disable(name)

    def enable(self, name: str) -> None:
        self._logger.enable(name)

    def configure(self, **kwargs) -> None:
        self._logger.configure(**kwargs)


_default_logger: Optional[PyLogexLogger] = None


def get_logger(config_path: Optional[Path] = None) -> PyLogexLogger:
    """Get logger instance (singleton pattern)."""
    global _default_logger, _configured

    if _default_logger is None:
        _default_logger = PyLogexLogger(config_path=config_path)
    elif config_path is not None:
        # Force reconfigure if config_path provided
        _configured = False
        get_config_manager().load_config(config_path)

    return _default_logger
