"""Default YAML configuration template for py_logex."""

DEFAULT_YAML_TEMPLATE = """# py_logex Configuration File
# Auto-generated - modify as needed

logger:
  file: "{script_name}.log"
  level: "INFO"
  rotation: "500 MB"
  retention: "10 days"
  compression: "zip"
  format: "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
  
  console:
    enabled: true
    level: "INFO"
"""


def get_default_yaml(script_name: str = "app") -> str:
    """
    Get default YAML configuration with script name substitution.

    Args:
        script_name: Name of the script (without .py extension)

    Returns:
        Default YAML configuration string
    """
    return DEFAULT_YAML_TEMPLATE.replace("{script_name}", script_name)
