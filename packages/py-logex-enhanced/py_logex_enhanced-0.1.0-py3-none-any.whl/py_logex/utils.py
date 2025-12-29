"""Utility functions for py_logex."""

import os
import sys
import inspect
from pathlib import Path
from typing import Optional, List


def get_script_name() -> str:
    """
    Get the name of the script that's running (without .py extension).

    Returns:
        Script name without extension
    """
    try:
        # Try to get the main script name
        if hasattr(sys.modules["__main__"], "__file__"):
            main_file = sys.modules["__main__"].__file__
            if main_file:
                return Path(main_file).stem

        # Fallback to caller's file
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_file = frame.f_back.f_code.co_filename
            return Path(caller_file).stem
    except Exception:
        pass

    return "app"


def get_caller_path() -> Path:
    """
    Get the directory path of the file that's importing py_logex.

    Returns:
        Path to caller's directory
    """
    try:
        frame = inspect.currentframe()
        if frame:
            # Walk up the stack to find the first frame outside py_logex package
            for outer_frame in inspect.getouterframes(frame):
                filename = outer_frame.filename
                if "py_logex" not in filename and "__init__.py" not in filename:
                    return Path(filename).resolve().parent
    except Exception:
        pass

    return Path.cwd()


def walk_up_find_file(
    filename: str, start_path: Optional[Path] = None, max_levels: int = 5
) -> Optional[Path]:
    """
    Walk up directory tree looking for a specific file.

    Args:
        filename: Name of file to find
        start_path: Starting directory (defaults to caller's directory)
        max_levels: Maximum number of parent directories to check

    Returns:
        Path to file if found, None otherwise
    """
    if start_path is None:
        start_path = get_caller_path()

    current = start_path
    for _ in range(max_levels):
        file_path = current / filename
        if file_path.exists() and file_path.is_file():
            return file_path

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def get_common_config_locations(filename: str = "logging.yaml") -> List[Path]:
    """
    Get list of common configuration file locations to check.

    Args:
        filename: Name of config file

    Returns:
        List of potential config file paths
    """
    cwd = Path.cwd()
    home = Path.home()

    locations = [
        cwd / filename,
        cwd / "config" / filename,
        cwd / "configs" / filename,
        cwd / "src" / "config" / filename,
        cwd / ".config" / filename,
        home / ".py_logex" / filename,
    ]

    return locations


def ensure_directory_exists(file_path: Path) -> None:
    """
    Ensure the directory for a file path exists.

    Args:
        file_path: Path to file
    """
    directory = file_path.parent
    directory.mkdir(parents=True, exist_ok=True)
