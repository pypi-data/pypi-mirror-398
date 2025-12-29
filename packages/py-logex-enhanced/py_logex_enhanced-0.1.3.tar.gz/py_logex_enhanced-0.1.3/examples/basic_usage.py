"""
Basic usage example for py_logex.

This example demonstrates the simplest way to use py_logex.
"""

from py_logex import logger

# Simple logging
logger.info("Application started")
logger.debug("This is a debug message")
logger.warning("This is a warning")
logger.error("This is an error")
logger.success("Operation completed successfully")

# Exception logging
try:
    result = 10 / 0
except Exception as e:
    logger.exception(e)

# With additional context
try:
    data = {"key": "value"}
    missing = data["nonexistent"]
except Exception as e:
    logger.exception(e, context={"data": data, "operation": "lookup"})

logger.info("Application finished")
