"""Configuration for Google SDK Store integration."""

from aixtools.utils.config_util import get_variable_env

POSTGRES_URL = str(get_variable_env("POSTGRES_URL", False))
