# py-logex-enhanced

**Simple, powerful logging with built-in exception handling and YAML configuration**

[![PyPI version](https://badge.fury.io/py/py-logex-enhanced.svg)](https://badge.fury.io/py/py-logex-enhanced)
[![Python Versions](https://img.shields.io/pypi/pyversions/py-logex-enhanced.svg)](https://pypi.org/project/py-logex-enhanced/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

`py-logex-enhanced` is a lightweight wrapper around [loguru](https://github.com/Delgan/loguru) that adds YAML-based configuration and enhanced exception handling, making it perfect for production environments.

---

## ✨ Features

- 🚀 **Zero Configuration** - Works out of the box with sensible defaults
- 📝 **YAML Configuration** - Flexible, easy-to-read configuration files
- 🔍 **Enhanced Exception Logging** - See exactly where errors occur (file, line, function)
- 🎯 **Multiple Loggers** - Different log files for different components
- 📄 **Auto-Discovery** - Finds config files automatically
- 💡 **Simple API** - Just like loguru, but easier
- 🛠️ **CLI Tools** - Manage configurations from command line

---

## 📦 Installation

```bash
pip install py-logex-enhanced
```

**Requirements:**
- Python >= 3.8
- loguru >= 0.7.0
- pyyaml >= 6.0

---

## 🚀 Quick Start

### Basic Usage

```python
from py_logex import logger

# Simple logging
logger.info("Application started")
logger.debug("Debug information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.success("Operation completed successfully")

# Exception handling with full traceback
try:
    result = 10 / 0
except Exception as e:
    logger.exception(e)
```

That's it! `py-logex-enhanced` automatically creates a `logging.yaml` config file and starts logging.

### Exception Logging Output

When you use `logger.exception()`, you get detailed error information:

```
2024-12-26 10:30:45 | ERROR    | main.py:process_data:23 - ZeroDivisionError: division by zero
Location: main.py:process_data:23
Code: result = 10 / 0

Traceback (most recent call last):
  File "/app/main.py", line 23, in process_data
    result = 10 / 0
ZeroDivisionError: division by zero
```

### Multiple Loggers

```python
from py_logex import get_logger

# Create different loggers for different components
app_logger = get_logger()           # Logs to app.log
db_logger = get_logger("database")  # Logs to database.log
api_logger = get_logger("api")      # Logs to api.log

app_logger.info("Application started")
db_logger.debug("Database query executed")
api_logger.warning("API rate limit approaching")
```

---

## ⚙️ Configuration

### Automatic Configuration

When you first import `py-logex-enhanced`, it automatically creates `logging.yaml` in your project root with sensible defaults:

```yaml
logger:
  file: "app.log"
  level: "INFO"
  rotation: "500 MB"
  retention: "10 days"
  compression: "zip"
  format: "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
  
  console:
    enabled: true
    level: "INFO"
```

### Custom Configuration

Create your own `logging.yaml`:

```yaml
logger:
  file: "myapp.log"
  level: "DEBUG"
  rotation: "100 MB"
  retention: "7 days"
  compression: "zip"
  
  console:
    enabled: true
    level: "INFO"

# Named loggers for different components
loggers:
  database:
    file: "database.log"
    level: "DEBUG"
    rotation: "50 MB"
  
  api:
    file: "api.log"
    level: "WARNING"
    console:
      enabled: false  # Disable console output for this logger
```

### Configuration Discovery

`py-logex-enhanced` finds your configuration automatically using this priority:

1. **Environment Variable**: `PYLOGEX_CONFIG=/path/to/logging.yaml`
2. **Walk Up**: Searches parent directories for `logging.yaml`
3. **Common Locations**: `./config/logging.yaml`, `./src/config/logging.yaml`, etc.
4. **Create Default**: Creates `logging.yaml` in current directory

---

## 🛠️ CLI Tools

`py-logex-enhanced` includes command-line tools for managing configurations:

```bash
# Show current configuration
py_logex config show

# Create new configuration file
py_logex config init

# Create with custom name
py_logex config init -n myapp

# Force overwrite existing file
py_logex config init --force

# Validate configuration
py_logex config validate

# Validate specific file
py_logex config validate -c /path/to/logging.yaml

# Show version
py_logex version
```

---

## 📚 Examples

Check out the [examples](examples/) directory for more:

### [basic_usage.py](examples/basic_usage.py)
Simple logging examples showing all log levels and exception handling.

### [multiple_loggers.py](examples/multiple_loggers.py)
Using multiple loggers for different components of your application.

### [custom_config.py](examples/custom_config.py)
Custom configurations and environment-specific setups.

---

## 🔧 Advanced Usage

### Environment-Specific Configuration

```python
import os
from pathlib import Path
from py_logex import get_logger

env = os.environ.get("ENVIRONMENT", "development")
config_file = f"./config/{env}-logging.yaml"

logger = get_logger(config_path=Path(config_file))
logger.info(f"Running in {env} mode")
```

### Reconfiguring at Runtime

```python
from py_logex import logger
from pathlib import Path

logger.info("Using original config")

# Switch to different config
logger.set_config(Path("./new_config.yaml"))
logger.info("Using new config")
```

### Docker/Production Setup

```dockerfile
# Dockerfile
ENV PYLOGEX_CONFIG=/app/config/production-logging.yaml
```

```python
# app.py - no changes needed!
from py_logex import logger

logger.info("Production logging configured automatically")
```

### Exception Logging with Context

```python
from py_logex import logger

try:
    user_id = 12345
    process_payment(user_id, amount=100)
except Exception as e:
    logger.exception(e, context={
        "user_id": user_id,
        "amount": 100,
        "operation": "payment_processing"
    })
```

---

## 🧪 Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=py_logex --cov-report=html

# Run specific test file
pytest tests/test_logger.py -v

# Run with verbose output
pytest -v
```

All tests are located in the `tests/` directory and cover:
- Logger functionality
- Configuration discovery
- CLI commands
- Exception handling

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Run tests** (`pytest`)
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Development Setup

```bash
# Clone the repository
git clone https://github.com/sherozshaikh/py-logex.git
cd py-logex

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black py_logex tests

# Run linting
flake8 py_logex tests
```

---

## 📖 Documentation

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `file` | string | `"app.log"` | Log file path |
| `level` | string | `"INFO"` | Minimum log level |
| `rotation` | string | `"500 MB"` | When to rotate log files |
| `retention` | string | `"10 days"` | How long to keep old logs |
| `compression` | string | `"zip"` | Compression format for old logs |
| `format` | string | See config | Log message format |
| `console.enabled` | boolean | `true` | Enable console output |
| `console.level` | string | `"INFO"` | Console log level |

### Log Levels

- `TRACE` - Very detailed debugging
- `DEBUG` - Detailed debugging information
- `INFO` - General information messages
- `SUCCESS` - Success messages
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical error messages

---

## 🤔 Why py-logex-enhanced?

| Feature | Standard Logging | loguru | py-logex-enhanced |
|---------|-----------------|--------|-------------------|
| Simple API | ❌ | ✅ | ✅ |
| YAML Config | ❌ | ❌ | ✅ |
| Auto-discovery | ❌ | ❌ | ✅ |
| Exception Details | ❌ | ⚠️ | ✅ |
| Multiple Loggers | ⚠️ | ⚠️ | ✅ |
| Zero Config | ❌ | ⚠️ | ✅ |
| CLI Tools | ❌ | ❌ | ✅ |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built on top of the excellent [loguru](https://github.com/Delgan/loguru) library
- Inspired by the need for simpler logging configuration in production environments

---

## 🐛 Bug Reports

Please report bugs on the [GitHub Issues](https://github.com/sherozshaikh/py-logex/issues) page.

When reporting a bug, please include:
- Python version
- py-logex-enhanced version
- Operating system
- Minimal code to reproduce the issue
- Expected behavior
- Actual behavior

---

## 💬 Support

- **Documentation**: [GitHub README](https://github.com/sherozshaikh/py-logex#readme)
- **Issues**: [GitHub Issues](https://github.com/sherozshaikh/py-logex/issues)
- **PyPI**: [https://pypi.org/project/py-logex-enhanced/](https://pypi.org/project/py-logex-enhanced/)
- **Email**: shaikh.sheroz07@gmail.com

---

## ⭐ Show Your Support

If you find this project useful, please consider giving it a star on GitHub!

[![GitHub stars](https://img.shields.io/github/stars/sherozshaikh/py-logex.svg?style=social&label=Star)](https://github.com/sherozshaikh/py-logex)

---

## 📊 Project Status

- **Status**: Active Development
- **Version**: 0.1.1
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12
- **License**: MIT

---

Made with ❤️ for the Python community
