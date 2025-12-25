"""
Logging utilities for model patching and request/response tracking.
"""

import functools
from contextlib import asynccontextmanager
from uuid import uuid4

from aixtools.logging.logging_config import get_logger
from aixtools.model_patch.model_patch import (
    ModelRawRequest,
    ModelRawRequestResult,
    ModelRawRequestYieldItem,
    get_request_fn,
    get_request_stream_fn,
    model_patch,
)

logger = get_logger(__name__)


def log_async_method(fn, agent_logger):
    """Log async method calls"""

    @functools.wraps(fn)
    async def model_request_logger_wrapper(*args, **kwargs):
        # Log request
        uuid = str(uuid4())  # Create a unique ID for this request
        log_object = ModelRawRequest(method_name=fn.__name__, request_id=uuid, args=args, kwargs=kwargs)
        await agent_logger.log(log_object)
        # Invoke the original method
        try:
            result = await fn(*args, **kwargs)
            # Log results
            log_object = ModelRawRequestResult(method_name=fn.__name__, request_id=uuid, result=result)
            await agent_logger.log(log_object)
        except Exception as e:
            # Log exception
            await agent_logger.log(e)
            raise e
        return result

    return model_request_logger_wrapper


def log_async_stream(fn, agent_logger):
    """Log async streaming method calls with individual item tracking."""

    @functools.wraps(fn)
    @asynccontextmanager
    async def model_request_stream_logger_wrapper(*args, **kwargs):
        # Log request
        uuid = str(uuid4())  # Create a unique ID for this request
        log_object = ModelRawRequest(method_name=fn.__name__, request_id=uuid, args=args, kwargs=kwargs)
        await agent_logger.log(log_object)
        # Invoke the original method
        async with fn(*args, **kwargs) as stream:

            async def gen():
                item_num = 0
                try:
                    async for item in stream:
                        # Log yielded items
                        log_object = ModelRawRequestYieldItem(
                            method_name=fn.__name__, request_id=uuid, item=item, item_num=item_num
                        )
                        await agent_logger.log(log_object)
                        item_num += 1
                        yield item
                except Exception as e:
                    # Log exception
                    await agent_logger.log(e)
                    raise e

            yield gen()

    return model_request_stream_logger_wrapper


def model_patch_logging(model, agent_logger):
    """Patch model with logging methods"""
    logger.debug("Patching model with logging")
    return model_patch(
        model,
        request_method=log_async_method(get_request_fn(model), agent_logger),
        request_stream_method=log_async_stream(get_request_stream_fn(model), agent_logger),
    )
