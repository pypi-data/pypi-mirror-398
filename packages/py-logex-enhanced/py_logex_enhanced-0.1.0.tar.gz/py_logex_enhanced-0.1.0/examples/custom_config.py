"""
Custom configuration example for py_logex.

This example demonstrates how to use custom configuration files
and environment variables.
"""

import os
from pathlib import Path
from py_logex import get_logger

# Example 1: Using environment variable
# Set this before running: export PYLOGEX_CONFIG=/path/to/custom/logging.yaml
if os.environ.get("PYLOGEX_CONFIG"):
    logger = get_logger()
    logger.info("Using config from environment variable")
else:
    logger = get_logger()
    logger.info("Using default config discovery")

# Example 2: Explicit config path
custom_config = Path("./config/logging.yaml")
if custom_config.exists():
    custom_logger = get_logger(config_path=custom_config)
    custom_logger.info("Using custom configuration file")

# Example 3: Reconfiguring at runtime
logger.info("Original configuration")

# Create a new config on the fly
new_config = Path("./new_logging.yaml")
if not new_config.exists():
    new_config.write_text("""
defaults:
  level: DEBUG
  console:
    enabled: true
    colorize: true

logger:
  file: reconfigured.log
  level: DEBUG
""")

logger.set_config(new_config)
logger.debug("After reconfiguration - this debug message should now appear")

# Example 4: Multiple configurations for different environments
environment = os.environ.get("ENVIRONMENT", "development")

config_map = {
    "development": "./config/dev-logging.yaml",
    "staging": "./config/staging-logging.yaml",
    "production": "./config/prod-logging.yaml",
}

config_file = config_map.get(environment)
if config_file and Path(config_file).exists():
    env_logger = get_logger(config_path=Path(config_file))
    env_logger.info(f"Running in {environment} mode")
else:
    logger.warning(f"Config for {environment} not found, using defaults")
