import os
from pathlib import Path

from google import genai

from aixtools.logging.logging_config import get_logger
from aixtools.utils.config import GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT, GOOGLE_GENAI_USE_VERTEXAI

logger = get_logger(__name__)


def get_genai_client(service_account_key_path: Path | None = None) -> genai.Client:
    """Initialize and return a Google GenAI client using Vertex AI / Gemini Developer API."""
    assert GOOGLE_CLOUD_PROJECT, "GOOGLE_CLOUD_PROJECT is not set"
    assert GOOGLE_CLOUD_LOCATION, "GOOGLE_CLOUD_LOCATION is not set"
    if service_account_key_path:
        if not service_account_key_path.exists():
            raise FileNotFoundError(f"Service account key file not found: {service_account_key_path}")
        logger.info(f"✅ GCP Service Account Key File: {service_account_key_path}")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(service_account_key_path)
    return genai.Client(
        vertexai=GOOGLE_GENAI_USE_VERTEXAI,
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
    )
