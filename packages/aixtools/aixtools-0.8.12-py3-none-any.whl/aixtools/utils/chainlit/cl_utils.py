"""
Utilities for Chainlit
"""

import inspect
from copy import deepcopy
from functools import wraps
from typing import Callable, List, Optional, Union

import pandas as pd
from chainlit import Step
from chainlit.context import get_context
from literalai.observability.step import TrueStepType

from aixtools.logging.logging_config import get_logger
from aixtools.utils.utils import truncate

logger = get_logger(__name__)

DEFAULT_SKIP_ARGS = ("self", "cls")

MAX_SIZE_STR = 10 * 1024
MAX_SIZE_DF_ROWS = 100


def is_chainlit() -> bool:
    """Are we running in chainlit?"""
    try:
        get_context()
        return True
    except Exception:
        return False


def flatten_args_kwargs(func, args, kwargs, skip_args=DEFAULT_SKIP_ARGS):
    signature = inspect.signature(func)
    bound_arguments = signature.bind(*args, **kwargs)
    bound_arguments.apply_defaults()
    return {k: deepcopy(v) for k, v in bound_arguments.arguments.items() if k not in skip_args}


def _step_name(func, args, kwargs):
    """
    Create a step name: class.method
    It detects the class name from the first method's argument.
    """
    if len(args) == 0:
        return func.__name__
    signature = inspect.signature(func)
    bound_arguments = signature.bind(*args, **kwargs)
    arguments = [(k, v) for k, v in bound_arguments.arguments.items()]
    arg0_name, arg0_value = arguments[0]
    if arg0_name == "self":
        return f"{arg0_value.__class__.__name__}.{func.__name__}"
    if arg0_name == "cls":
        return f"{arg0_value.__name__}.{func.__name__}"
    return func.__name__


def limit_size(data):
    """ """
    if isinstance(data, str):
        return truncate(data, max_len=MAX_SIZE_STR)
    if isinstance(data, pd.DataFrame):
        if len(data) > MAX_SIZE_DF_ROWS:
            return data.head(MAX_SIZE_DF_ROWS)
    return data


def cl_step(  # noqa: PLR0913
    original_function: Optional[Callable] = None,
    *,
    name: Optional[str] = "",
    type: TrueStepType = "undefined",
    id: Optional[str] = None,
    parent_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    language: Optional[str] = None,
    show_input: Union[bool, str] = "json",
    default_open: bool = False,
):
    """
    Step decorator for async and sync functions and methods (they ignore the self argument).
    It deactivates if not within a Chainlit context.
    """

    def wrapper(func: Callable):
        # Handle async decorator
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                nonlocal name
                if not name:
                    name = _step_name(func, args, kwargs)
                if is_chainlit():
                    async with Step(
                        type=type,
                        name=name,
                        id=id,
                        parent_id=parent_id,
                        tags=tags,
                        language=language,
                        show_input=show_input,
                        default_open=default_open,
                    ) as step:
                        try:
                            step.input = flatten_args_kwargs(func, args, kwargs)
                        except Exception as e:
                            logger.exception(e)
                        result = await func(*args, **kwargs)
                        try:
                            if result and not step.output:
                                step.output = limit_size(result)
                        except Exception as e:
                            step.is_error = True
                            step.output = str(e)
                        return result
                else:
                    # If not in Chainlit, just call the function
                    result = await func(*args, **kwargs)
                    print(f"Function '{func.__name__}' called with args: {args}, kwargs: {kwargs}, result: {result}")
                    return result

            return async_wrapper
        else:
            # Handle sync decorator
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                nonlocal name
                if not name:
                    name = _step_name(func, args, kwargs)
                if is_chainlit():
                    with Step(
                        type=type,
                        name=name,
                        id=id,
                        parent_id=parent_id,
                        tags=tags,
                        language=language,
                        show_input=show_input,
                        default_open=default_open,
                    ) as step:
                        try:
                            step.input = flatten_args_kwargs(func, args, kwargs)
                        except Exception as e:
                            logger.exception(e)
                        result = func(*args, **kwargs)
                        try:
                            if result and not step.output:
                                step.output = limit_size(result)
                        except Exception as e:
                            step.is_error = True
                            step.output = str(e)
                        return result
                else:
                    # If not in Chainlit, just call the function
                    result = func(*args, **kwargs)
                    print(f"Function '{func.__name__}' called with args: {args}, kwargs: {kwargs}, result: {result}")
                    return result

            return sync_wrapper

    func = original_function
    if not func:
        return wrapper
    else:
        return wrapper(func)
