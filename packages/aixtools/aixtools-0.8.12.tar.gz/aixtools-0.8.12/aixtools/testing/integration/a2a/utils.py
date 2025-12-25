"""Utility functions for A2A testing integration."""

import importlib
from pathlib import Path
from typing import Callable

from a2a.server.agent_execution import RequestContext

from aixtools.a2a.google_sdk.pydantic_ai_adapter.storage import PydanticAiAgentHistoryStorage
from aixtools.testing.aix_test_model import AixTestModel

METADATA_TEST_USE_CASE_KEY = "test_use_case"


def get_test_mode_use_case(context: RequestContext) -> str | None:
    """Retrieve the test use case from the request context metadata."""
    if not context.message or not context.message.metadata:
        return None

    return context.message.metadata.get(METADATA_TEST_USE_CASE_KEY, None)


def discover_test_models(models_path: Path, package_name: str) -> dict[str, Callable]:
    """Discover all model_test_* functions from Python scripts in a directory.

    Args:
        models_path: Path to the folder containing model test Python files.
        package_name: The Python package name for importing modules (e.g., "img_gen.a2a.test_integration.fake_llm").

    Returns:
        A dictionary mapping test names (without 'model_test_' prefix) to their functions.
    """
    return {
        attr.replace("model_test_", "", 1): getattr(module, attr)
        for file in models_path.glob("*.py")
        if file.stem != "__init__"
        for module in [importlib.import_module(f"{package_name}.{file.stem}")]
        for attr in dir(module)
        if attr.startswith("model_test_")
    }


AixTestModelFactory = Callable[[RequestContext, PydanticAiAgentHistoryStorage], AixTestModel]
