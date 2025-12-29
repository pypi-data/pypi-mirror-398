"""Tests for exception handling."""

import pytest
from py_logex.exceptions import (
    ExceptionFormatter,
    format_exception_for_logging,
)


def test_format_exception_basic():
    """Test basic exception formatting."""
    try:
        raise ValueError("Test error message")
    except Exception as e:
        formatted = ExceptionFormatter.format_exception(e)

        assert "ValueError" in formatted
        assert "Test error message" in formatted
        assert "Traceback" in formatted


def test_format_exception_with_traceback():
    """Test exception formatting with traceback."""

    def level3():
        raise RuntimeError("Deep error")

    def level2():
        level3()

    def level1():
        level2()

    try:
        level1()
    except Exception as e:
        formatted = ExceptionFormatter.format_exception(e)

        assert "RuntimeError" in formatted
        assert "level3" in formatted
        assert "level2" in formatted
        assert "level1" in formatted


def test_get_exception_context():
    """Test extracting exception context."""
    try:
        x = 1 / 0
    except Exception as e:
        context = ExceptionFormatter.get_exception_context(e)

        assert context["type"] == "ZeroDivisionError"
        assert "division" in context["message"].lower()
        assert context["file"] is not None
        assert context["line"] is not None
        assert context["function"] == "test_get_exception_context"


def test_exception_context_with_code():
    """Test that exception context includes code snippet."""
    try:
        result = int("not a number")
    except Exception as e:
        context = ExceptionFormatter.get_exception_context(e)

        assert context["code"] is not None
        assert "int" in context["code"]


def test_format_exception_for_logging():
    """Test formatting exception specifically for logging."""
    try:
        raise KeyError("missing_key")
    except Exception as e:
        formatted = format_exception_for_logging(e)

        assert "KeyError" in formatted
        assert "missing_key" in formatted
        assert "Location:" in formatted
        assert "Traceback" in formatted


def test_format_exception_with_context():
    """Test formatting exception with additional context."""
    try:
        raise ValueError("Invalid input")
    except Exception as e:
        context = {"user_id": 123, "action": "update"}
        formatted = format_exception_for_logging(e, context=context)

        assert "ValueError" in formatted
        assert "Context:" in formatted
        assert "user_id" in formatted


def test_format_exception_different_levels():
    """Test formatting exception at different log levels."""
    try:
        raise Exception("Test")
    except Exception as e:
        debug_fmt = format_exception_for_logging(e, level="DEBUG")
        error_fmt = format_exception_for_logging(e, level="ERROR")

        assert "Exception" in debug_fmt
        assert "Exception" in error_fmt


def test_exception_no_traceback():
    """Test handling exception without traceback."""
    exc = ValueError("No traceback")
    context = ExceptionFormatter.get_exception_context(exc)

    assert context["type"] == "ValueError"
    assert context["message"] == "No traceback"
    assert context["file"] is None
    assert context["line"] is None


def test_nested_exceptions():
    """Test formatting nested exceptions."""

    def inner():
        raise ValueError("Inner error")

    def outer():
        try:
            inner()
        except ValueError as e:
            raise RuntimeError("Outer error") from e

    try:
        outer()
    except Exception as e:
        formatted = ExceptionFormatter.format_exception(e)

        assert "RuntimeError" in formatted
        assert "Outer error" in formatted


def test_exception_with_special_characters():
    """Test exception with special characters in message."""
    try:
        raise Exception("Error with 'quotes' and \"double quotes\" and <brackets>")
    except Exception as e:
        formatted = format_exception_for_logging(e)

        assert "quotes" in formatted
        assert "double quotes" in formatted
        assert "brackets" in formatted


def test_exception_multiline_message():
    """Test exception with multiline message."""
    message = """This is a
multiline
error message"""

    try:
        raise ValueError(message)
    except Exception as e:
        formatted = format_exception_for_logging(e)

        assert "multiline" in formatted
        assert "error message" in formatted


def test_exception_context_file_name_only():
    """Test that exception context includes just filename, not full path."""
    try:
        raise Exception("Test")
    except Exception as e:
        context = ExceptionFormatter.get_exception_context(e)

        # Should have filename without path
        assert context["file"] is not None
        assert "/" not in context["file"] or context["file"].count("/") == 0

        # But full path should be available
        assert context["full_path"] is not None
