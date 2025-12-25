from typing import Any

from pydantic import BaseModel, ConfigDict

from aixtools.logging.logging_config import get_logger

logger = get_logger(__name__)


class ModelRawRequest(BaseModel):
    method_name: str  # Model method name
    request_id: str  # Unique request ID
    args: tuple  # Method arguments
    kwargs: dict  # Method keyword arguments


class ModelRawRequestResult(BaseModel):
    method_name: str  # Model method name
    request_id: str  # Unique request ID
    result: Any  # Method's result

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ModelRawRequestYieldItem(BaseModel):
    method_name: str  # Model method name
    request_id: str  # Unique request ID
    item_num: int  # Item number in the stream
    item: Any  # Yielded item

    model_config = ConfigDict(arbitrary_types_allowed=True)


def get_request_fn(model):
    """Get the original request method"""
    if is_patched(model):
        return model._request_ori
    return model.request


def get_request_stream_fn(model):
    """Get the original request method"""
    if is_patched(model):
        return model._request_stream_ori
    return model.request_stream


def is_patched(model):
    return hasattr(model, "_request_ori") or hasattr(model, "_request_stream_ori")


def model_patch(model, request_method, request_stream_method):
    """Replace model.request and model.request_stream with logging versions"""
    if is_patched(model):
        logger.warning(f"Model {model.__class__.__name__} is already patched. Skipping patching.")
        return model
    # Save original methods
    model._request_ori = model.request
    model._request_stream_ori = model.request_stream
    # Patch methods
    model.request = request_method
    model.request_stream = request_stream_method
    return model
