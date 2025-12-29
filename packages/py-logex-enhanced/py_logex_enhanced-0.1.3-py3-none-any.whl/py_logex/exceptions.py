"""Enhanced exception handling for py_logex."""

import sys
import traceback
from typing import Optional, Any
from pathlib import Path


class ExceptionFormatter:
    """Formats exceptions with enhanced file/line information."""

    @staticmethod
    def format_exception(
        exc: Exception, include_locals: bool = True, max_frames: Optional[int] = None
    ) -> str:
        """
        Format exception with detailed traceback information.

        Args:
            exc: Exception to format
            include_locals: Whether to include local variables
            max_frames: Maximum number of frames to include (None for all)

        Returns:
            Formatted exception string
        """
        exc_type = type(exc).__name__
        exc_msg = str(exc)

        # Get traceback
        tb = exc.__traceback__
        if tb is None:
            return f"{exc_type}: {exc_msg}"

        # Extract frames
        frames = traceback.extract_tb(tb)
        if max_frames:
            frames = frames[-max_frames:]

        # Build formatted output
        lines = [f"\n{exc_type}: {exc_msg}"]
        lines.append("\nTraceback (most recent call last):")

        for frame in frames:
            file_path = Path(frame.filename)

            # Format frame info
            lines.append(f'  File "{file_path}", line {frame.lineno}, in {frame.name}')
            if frame.line:
                lines.append(f"    {frame.line.strip()}")

        # Add exception line again at the end
        lines.append(f"\n{exc_type}: {exc_msg}")

        return "\n".join(lines)

    @staticmethod
    def get_exception_context(exc: Exception) -> dict:
        """
        Extract context information from exception.

        Args:
            exc: Exception to extract context from

        Returns:
            Dictionary with exception context
        """
        tb = exc.__traceback__
        if tb is None:
            return {
                "type": type(exc).__name__,
                "message": str(exc),
                "file": None,
                "line": None,
                "function": None,
            }

        # Get the last frame (where exception occurred)
        frames = traceback.extract_tb(tb)
        if frames:
            last_frame = frames[-1]
            return {
                "type": type(exc).__name__,
                "message": str(exc),
                "file": str(Path(last_frame.filename).name),
                "full_path": last_frame.filename,
                "line": last_frame.lineno,
                "function": last_frame.name,
                "code": last_frame.line.strip() if last_frame.line else None,
            }

        return {
            "type": type(exc).__name__,
            "message": str(exc),
            "file": None,
            "line": None,
            "function": None,
        }


def format_exception_for_logging(
    exc: Exception, level: str = "ERROR", context: Optional[dict] = None
) -> str:
    """
    Format exception specifically for logging output.

    Args:
        exc: Exception to format
        level: Log level
        context: Additional context to include

    Returns:
        Formatted string for logging
    """
    formatter = ExceptionFormatter()
    exc_context = formatter.get_exception_context(exc)

    # Build message
    parts = []

    # Exception type and message
    parts.append(f"{exc_context['type']}: {exc_context['message']}")

    # Location info
    if exc_context["file"]:
        location = f"{exc_context['file']}"
        if exc_context["function"]:
            location += f":{exc_context['function']}"
        if exc_context["line"]:
            location += f":{exc_context['line']}"
        parts.append(f"Location: {location}")

    # Code snippet
    if exc_context["code"]:
        parts.append(f"Code: {exc_context['code']}")

    # Full traceback
    parts.append("\n" + formatter.format_exception(exc))

    # Additional context
    if context:
        parts.append(f"\nContext: {context}")

    return "\n".join(parts)
