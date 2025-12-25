"""
Configuration settings and environment variables for the application.
"""

import logging
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

from aixtools.utils.config_util import (
    find_env_file,
    get_project_root,
    get_secret_from_aws_params_store,
    get_variable_env,
)
from aixtools.utils.utils import str2bool

# Debug mode
LOG_LEVEL = logging.DEBUG

# Set up some environment variables (there are usually set up by 'config.sh')

# This file's path
FILE_PATH = Path(__file__).resolve()

# This project's root directory (AixTools)
# if installed as a package, it will be `.venv/lib/python3.x/site-packages/aixtools`
PROJECT_DIR = FILE_PATH.parent.parent.parent.resolve()

# Get the main project directory (the one project that is using this package)
PROJECT_ROOT = get_project_root()

# From the environment variables


# Iterate over all parents of FILE_PATH to find .env files
def all_parents(path: Path):
    """Yield all parent directories of a given path."""
    while path.parent != path:
        yield path
        path = path.parent


# Set up environment search path
# Start with the most specific (current directory) and expand outward
env_dirs = [Path.cwd(), PROJECT_ROOT, FILE_PATH.parent]
env_file = find_env_file(env_dirs)

if env_file:
    logging.info("Using .env file at '%s'", env_file)
    # Load the environment variables from the found .env file
    load_dotenv(env_file)
    # Assign project dir based on the .env file
    MAIN_PROJECT_DIR = Path(env_file).parent
    logging.info("Using MAIN_PROJECT_DIR='%s'", MAIN_PROJECT_DIR)
    # Assign variables in '.env' global python environment
    env_vars = dotenv_values(env_file)
    globals().update(env_vars)

    # IMPORTANT: ensure VAULT_TOKEN is handled lazily, not as a raw .env global
    # via __getattr__ and decrypted instead of using the raw .env value.
    if "VAULT_TOKEN" in globals():
        del globals()["VAULT_TOKEN"]
else:
    logging.warning("No '.env' file found in any of the search paths, or their parents: %s", env_dirs)
    # Use PROJECT_ROOT as fallback
    MAIN_PROJECT_DIR = PROJECT_ROOT


# ---
# Directories
# ---
SCRIPTS_DIR = MAIN_PROJECT_DIR / "scripts"
DATA_DIR = Path(get_variable_env("DATA_DIR") or MAIN_PROJECT_DIR / "data")
DATA_DB_DIR = Path(get_variable_env("DATA_DB_DIR") or DATA_DIR / "db")
LOGS_DIR = MAIN_PROJECT_DIR / "logs"
PROMPTS_DIR = Path(get_variable_env("PROMPTS_DIR") or MAIN_PROJECT_DIR / "prompts")

logging.warning("Using         DATA_DIR='%s'", DATA_DIR)

# Vector database
VDB_CHROMA_PATH = DATA_DB_DIR / "chroma.db"
VDB_DEFAULT_SIMILARITY_THRESHOLD = 0.85

# ---
# Variables in '.env' file
# Explicitly load specific variables
# ---

MODEL_TIMEOUT = int(get_variable_env("MODEL_TIMEOUT", default="120"))  # type: ignore

MODEL_FAMILY = get_variable_env("MODEL_FAMILY")

# Azure models
AZURE_MODEL_NAME = get_variable_env("AZURE_MODEL_NAME")
AZURE_OPENAI_ENDPOINT = get_variable_env("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = get_variable_env("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = get_variable_env("AZURE_OPENAI_API_VERSION")

# OpenAI models
OPENAI_API_KEY = get_variable_env("OPENAI_API_KEY")
OPENAI_MODEL_NAME = get_variable_env("OPENAI_MODEL_NAME")

# Ollama models
OLLAMA_URL = get_variable_env("OLLAMA_URL")
OLLAMA_MODEL_NAME = get_variable_env("OLLAMA_MODEL_NAME")

# OpenRouter models
OPENROUTER_API_KEY = get_variable_env("OPENROUTER_API_KEY")
OPENROUTER_API_URL = get_variable_env("OPENROUTER_API_URL", default="https://openrouter.ai/api/v1")
OPENROUTER_MODEL_NAME = get_variable_env("OPENROUTER_MODEL_NAME")

# Embeddings
VDB_EMBEDDINGS_MODEL_FAMILY = get_variable_env("VDB_EMBEDDINGS_MODEL_FAMILY")
OPENAI_VDB_EMBEDDINGS_MODEL_NAME = get_variable_env("OPENAI_VDB_EMBEDDINGS_MODEL_NAME")
AZURE_VDB_EMBEDDINGS_MODEL_NAME = get_variable_env("AZURE_VDB_EMBEDDINGS_MODEL_NAME")
OLLAMA_VDB_EMBEDDINGS_MODEL_NAME = get_variable_env("OLLAMA_VDB_EMBEDDINGS_MODEL_NAME")

# Bedrock models
AWS_ACCESS_KEY_ID = get_variable_env("AWS_ACCESS_KEY_ID", allow_empty=True)
AWS_SECRET_ACCESS_KEY = get_variable_env("AWS_SECRET_ACCESS_KEY", allow_empty=True)
AWS_SESSION_TOKEN = get_variable_env("AWS_SESSION_TOKEN", allow_empty=True)
AWS_REGION = get_variable_env("AWS_REGION", allow_empty=True, default="us-east-1")
AWS_PROFILE = get_variable_env("AWS_PROFILE", allow_empty=True)
BEDROCK_MODEL_NAME = get_variable_env("BEDROCK_MODEL_NAME", allow_empty=True)
BEDROCK_CLAUDE_SONNET_1M_TOKENS = str2bool(
    get_variable_env("BEDROCK_CLAUDE_SONNET_1M_TOKENS", allow_empty=True, default="False")
)

# LogFire
LOGFIRE_TOKEN = get_variable_env("LOGFIRE_TOKEN", True, "")
LOGFIRE_TRACES_ENDPOINT = get_variable_env("LOGFIRE_TRACES_ENDPOINT", True, "")

# Google Vertex AI
GOOGLE_GENAI_USE_VERTEXAI = str2bool(get_variable_env("GOOGLE_GENAI_USE_VERTEXAI", True, True))
GOOGLE_CLOUD_PROJECT = get_variable_env("GOOGLE_CLOUD_PROJECT", True)
GOOGLE_CLOUD_LOCATION = get_variable_env("GOOGLE_CLOUD_LOCATION", True)


# OAuth parameters
APP_SECRET_ID = get_variable_env("APP_SECRET_ID")
APP_CLIENT_ID = get_variable_env("APP_CLIENT_ID")

# used for token audience check
APP_API_ID = get_variable_env("APP_API_ID")
APP_TENANT_ID = get_variable_env("APP_TENANT_ID")
AUTH_REDIRECT_URI = get_variable_env("AUTH_REDIRECT_URI", default="http://localhost:4444/direct-callback")
# used for token authorization check
APP_AUTHORIZED_GROUPS = get_variable_env("APP_AUTHORIZED_GROUPS", allow_empty=True)

# used to skip authorization in local tests if required.
SKIP_MCP_AUTHORIZATION = str2bool(get_variable_env("SKIP_MCP_AUTHORIZATION", True, False))
APP_DEFAULT_SCOPE = get_variable_env("APP_DEFAULT_SCOPE", allow_empty=True)

AUTH_TEST_TOKEN = get_variable_env("AUTH_TEST_TOKEN", allow_empty=True)

MCP_TOOLS_MAX_RETRIES = int(get_variable_env("MCP_TOOLS_MAX_RETRIES", default=10))

# File attachment limits and supported types for model context
MAX_EXTRACTED_TEXT_TOKENS = int(get_variable_env("MAX_EXTRACTED_TEXT_TOKENS", default=str(5_000)))
MAX_IMAGE_ATTACHMENT_SIZE = int(get_variable_env("MAX_IMAGE_ATTACHMENT_SIZE", default=str(2 * 1024 * 1024)))
# Image MIME types that can be attached to model context
IMAGE_ATTACHMENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
}
# Document MIME types that can be extracted as text
EXTRACTABLE_DOCUMENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",  # .xls
    "application/pdf",  # .pdf
}

# Context agent configuration
MAX_TOKENS_PER_FILE = int(get_variable_env("MAX_TOKENS_PER_FILE", default="5000"))
MAX_TOTAL_OUTPUT = int(get_variable_env("MAX_TOTAL_OUTPUT", default="50000"))
MAX_LINES = int(get_variable_env("MAX_LINES", default="200"))
MAX_LINE_LENGTH = int(get_variable_env("MAX_LINE_LENGTH", default="1000"))
MAX_CELL_LENGTH = int(get_variable_env("MAX_CELL_LENGTH", default="500"))
MAX_COLUMNS = int(get_variable_env("MAX_COLUMNS", default="50"))
DEFAULT_ROWS_HEAD = int(get_variable_env("DEFAULT_ROWS_HEAD", default="20"))
DEFAULT_ROWS_MIDDLE = int(get_variable_env("DEFAULT_ROWS_MIDDLE", default="10"))
DEFAULT_ROWS_TAIL = int(get_variable_env("DEFAULT_ROWS_TAIL", default="10"))
MAX_STRING_VALUE_LENGTH = int(get_variable_env("MAX_STRING_VALUE_LENGTH", default="500"))
MAX_ARRAY_ITEMS = int(get_variable_env("MAX_ARRAY_ITEMS", default="50"))
MAX_OBJECT_KEYS = int(get_variable_env("MAX_OBJECT_KEYS", default="50"))
MAX_OBJECT_STRING_LENGTH = int(get_variable_env("MAX_OBJECT_STRING_LENGTH", default="2000"))
MAX_NESTING_DEPTH = int(get_variable_env("MAX_NESTING_DEPTH", default="5"))

# Audio processing
DEFAULT_AUDIO_DURATION = float(get_variable_env("DEFAULT_AUDIO_DURATION", default="30.0"))
DEFAULT_AUDIO_HEAD_DURATION = float(get_variable_env("DEFAULT_AUDIO_HEAD_DURATION", default="10.0"))
DEFAULT_AUDIO_TAIL_DURATION = float(get_variable_env("DEFAULT_AUDIO_TAIL_DURATION", default="10.0"))
MAX_AUDIO_SIZE = int(get_variable_env("MAX_AUDIO_SIZE", default=str(10 * 1024 * 1024)))

# Vault parameters
VAULT_ADDRESS = get_variable_env("VAULT_ADDRESS", default="http://localhost:8200")
VAULT_ENV = get_variable_env("VAULT_ENV", allow_empty=True)
VAULT_MOUNT_POINT = get_variable_env("VAULT_MOUNT_POINT", allow_empty=True)
VAULT_PATH_PREFIX = get_variable_env("VAULT_PATH_PREFIX", allow_empty=True)
# read vault token from AWS Parameter Store
VAULT_AWS_SECRET_PATH = get_variable_env("VAULT_AWS_SECRET_PATH", allow_empty=True)
# AWS profile for using EC2 role
VAULT_AWS_PROFILE = get_variable_env("VAULT_AWS_PROFILE", allow_empty=True)


class VaultConfigError(RuntimeError):
    """Raised when VAULT_TOKEN is accessed but Vault/crypto config is invalid."""


# Cache for the real token
class VaultTokenCache:  # pylint: disable=too-few-public-methods
    """Cache for the real token."""

    VAULT_TOKEN: str = None


def _get_vault_token() -> str | None:
    """Get VAULT_TOKEN from AWS Parameter Store if configured, otherwise from env."""
    if VaultTokenCache.VAULT_TOKEN:
        return VaultTokenCache.VAULT_TOKEN

    if VAULT_AWS_SECRET_PATH:
        token = get_secret_from_aws_params_store(VAULT_AWS_SECRET_PATH, VAULT_AWS_PROFILE)
    else:
        token = get_variable_env("VAULT_TOKEN", allow_empty=True)

    VaultTokenCache.VAULT_TOKEN = token

    return token


def __getattr__(name: str):
    """getattr hook for VAULT_TOKEN."""
    if name == "VAULT_TOKEN":
        return _get_vault_token()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """dir hook for VAULT_TOKEN."""
    return sorted(list(globals().keys()) + ["VAULT_TOKEN"])
