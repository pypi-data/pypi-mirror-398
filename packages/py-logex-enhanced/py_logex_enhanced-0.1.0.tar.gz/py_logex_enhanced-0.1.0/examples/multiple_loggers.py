"""
Multiple loggers example for py_logex.

This example shows how to use multiple loggers for different parts of your application.
"""

from py_logex import get_logger

# Create different loggers for different components
app_logger = get_logger()
db_logger = get_logger("database")
api_logger = get_logger("api")

# Each logger writes to its own file
app_logger.info("Main application started")

# Simulate database operations
db_logger.info("Connecting to database")
db_logger.debug("Executing query: SELECT * FROM users")
db_logger.success("Query completed successfully")

# Simulate API calls
api_logger.info("API server starting on port 8000")
api_logger.debug("Registering endpoints")

# Error handling in different components
try:
    # Simulate database error
    raise ConnectionError("Database connection failed")
except Exception as e:
    db_logger.exception(e)

try:
    # Simulate API error
    raise ValueError("Invalid API request")
except Exception as e:
    api_logger.exception(e, level="WARNING")

app_logger.info("Application shutdown complete")
