"""
Centralized logging configuration for AixTools, based on Python's standard logging.
"""

import json
import logging
import logging.config
import os
import sys
import time
from pathlib import Path

# PyYAML is an optional dependency.
try:
    import yaml
except ImportError:
    yaml = None

# --- Default Configuration ---

logging.Formatter.converter = time.gmtime

DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "context_filter": {
            "()": "aixtools.logfilters.context_filter.ContextFilter",
        }
    },
    "formatters": {
        "color": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(asctime)s.%(msecs)03d %(levelname)-8s%(reset)s %(context)s[%(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        },
    },
    "handlers": {
        "stream": {
            "class": "colorlog.StreamHandler",
            "formatter": "color",
            "level": "INFO",
            "filters": ["context_filter"],
        },
    },
    "root": {
        "handlers": ["stream"],
        "level": "INFO",
    },
}

# --- Public API ---

get_logger = logging.getLogger


def configure_logging():
    """
    Configure the logging system.

    This function loads the logging configuration from a file or uses the
    hardcoded default. The configuration source is determined in the
    following order of precedence:

    1. LOGGING_CONFIG_PATH environment variable.
    2. logging.yaml in the current working directory.
    3. logging.json in the current working directory.
    4. Hardcoded default configuration.

    Special handling for pytest: If running under pytest without explicit
    log flags, console logging is suppressed to avoid interfering with
    pytest's own log capture mechanism.
    """
    # Detect if running under pytest and suppress console logging unless explicitly requested
    is_pytest = "pytest" in sys.modules or "pytest" in sys.argv[0] if sys.argv else False

    # Check for live log flags - handle both separate and combined flags
    wants_live_logs = False
    if sys.argv:
        for arg in sys.argv:
            # Check for explicit --log-cli
            if arg == "--log-cli":
                wants_live_logs = True
                break
            # Check for -s either standalone or combined with other flags (like -vsk, -vs, etc.)
            if arg.startswith("-") and not arg.startswith("--") and "s" in arg:
                wants_live_logs = True
                break

    if is_pytest and not wants_live_logs:
        # Use a minimal configuration that doesn't output to console during pytest
        pytest_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                }
            },
            "handlers": {
                # Only use NullHandler to suppress console output but allow pytest log capture
                "null": {
                    "class": "logging.NullHandler",
                }
            },
            "root": {
                "handlers": ["null"],
                "level": "INFO",
            },
        }
        logging.config.dictConfig(pytest_config)
        return

    config_path_str = os.environ.get("LOGGING_CONFIG_PATH")

    if config_path_str:
        config_path = Path(config_path_str)
        if not config_path.exists():
            raise FileNotFoundError(f"Logging configuration file not found: {config_path}")
        _load_config_from_file(config_path)
        return

    # Check for default config files in the current directory
    for filename in ["logging.yaml", "logging.json"]:
        config_path = Path.cwd() / filename
        if config_path.exists():
            _load_config_from_file(config_path)
            return

    # Fallback to the default configuration
    logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)


def _load_config_from_file(path: Path):
    """Load a logging configuration from a YAML or JSON file."""
    if path.suffix in [".yaml", ".yml"] and yaml:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
    elif path.suffix == ".json":
        config = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError(
            f"Unsupported configuration file format: {path.suffix}. "
            "Please use .yaml or .json. "
            "For YAML support, ensure PyYAML is installed (`uv add pyyaml`)."
        )

    if config:
        logging.config.dictConfig(config)


# --- Initial Configuration ---

# Automatically configure logging when the module is imported.
configure_logging()
