"""
Mock tool implementation for testing agent interactions.
"""

import functools
import inspect
from typing import Any, Awaitable, Callable, List, TypeVar, Union

T = TypeVar("T")


def mock_tool(func: Callable[..., Union[T, Awaitable[T]]], return_values: List[Any]) -> Callable[..., Any]:
    """
    Creates a mock version of the provided function that returns values from a predefined list.
    Supports both synchronous and asynchronous functions.

    Args:
        func: The original function to mock (can be sync or async)
        return_values: A list of values to be returned sequentially on each call

    Returns:
        A new function with the same signature and docstring as the original function,
        but returns values from the provided list sequentially.
        If the original function is async, the mock will also be async.

    Raises:
        IndexError: When the mock function is called more times than there are return values
    """
    # Make a copy of the return values to avoid modifying the original list
    values = return_values.copy()

    # Check if the function is asynchronous
    is_async = inspect.iscoroutinefunction(func)

    if is_async:
        # Create an async wrapper for async functions
        @functools.wraps(func)
        async def async_mock_wrapper(*args, **kwargs):  # pylint: disable=unused-argument
            # Check if we have any return values left
            if not values:
                raise IndexError(
                    f"No more mock return values available for {func.__name__}. "
                    f"The function has been called more times than the number of provided return values."
                )

            # Return and remove the first value from our list
            return values.pop(0)

        # Return the async wrapper function
        return async_mock_wrapper

    # Create a sync wrapper for sync functions
    @functools.wraps(func)
    def sync_mock_wrapper(*args, **kwargs):  # pylint: disable=unused-argument
        # Check if we have any return values left
        if not values:
            raise IndexError(
                f"No more mock return values available for {func.__name__}. "
                f"The function has been called more times than the number of provided return values."
            )

        # Return and remove the first value from our list
        return values.pop(0)

    # Return the sync wrapper function
    return sync_mock_wrapper
