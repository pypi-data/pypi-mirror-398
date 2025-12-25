"""
This module is useful for testing, so that we can run tests without having to call the real function.
The cached values are stored in `cache_file`.

In `learn=False` mode:
    - The model_request_cache_wrapper first tries to answer from the cached value.
    - If the cached value does not exist, it raises an exception.

In `learn=True` mode:
    - The model_request_cache_wrapper first tries to answer from the cached value.
    - If the cached value does not exist, it invokes the real function
      and adds the new result to `cache_file` for future use.

Values are saved to pickle files, but since objects could be non-picklable, we use `safe_deepcopy_for_cache`.
"""

import datetime
import functools
import hashlib
import json
import pickle
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Set, Tuple, Type

from aixtools.logging.log_objects import safe_deepcopy
from aixtools.logging.logging_config import get_logger
from aixtools.model_patch.model_patch import get_request_fn, get_request_stream_fn, model_patch

logger = get_logger(__name__)


class CacheKeyError(Exception):
    """Exception raised when a key is not found in the cache."""


def safe_deepcopy_for_cache_key(obj: Any, normalize_types: Set[Type] = None) -> Any:
    """
    A modified version of safe_deepcopy that normalizes or skips fields based on their types.
    This is useful for generating cache keys where some fields (like timestamps, UUIDs)
    should be normalized to ensure consistent cache hits.

    Args:
        obj: The object to copy
        normalize_types: Set of types to normalize (replace with placeholders)

    Returns:
        A deep copy of the object with normalized values for specified types
    """
    # Default types to normalize if none provided
    if normalize_types is None:
        normalize_types = {datetime.datetime, datetime.date, datetime.time, uuid.UUID}

    # Check if the object is of a type that should be normalized
    if any(isinstance(obj, t) for t in normalize_types):
        # Replace with a placeholder indicating the type
        return f"<{type(obj).__name__}>"

    # Check if the object is primitive (int, float, str, bool)
    if isinstance(obj, (int, float, str, bool)):
        return obj

    # Handle mappings (dict and other mapping types)
    if isinstance(obj, Mapping):
        return {k: safe_deepcopy_for_cache_key(v, normalize_types) for k, v in obj.items()}

    # Handle sequences (list, tuple, and other sequence types) but not strings
    if isinstance(obj, Sequence) and not isinstance(obj, str):
        return [safe_deepcopy_for_cache_key(item, normalize_types) for item in obj]

    # Handle objects with __dict__ attribute (custom classes)
    if hasattr(obj, "__dict__"):
        # For objects, we create a dictionary representation
        result = {}
        for attr, value in vars(obj).items():
            result[attr] = safe_deepcopy_for_cache_key(value, normalize_types)
        return result

    # For other types, return a string representation
    return f"<{type(obj).__name__}>"


def generate_cache_key(method_name: str, args: Tuple, kwargs: Dict) -> str:
    """
    Generate a unique cache key based on the method name and its arguments.
    Uses safe_deepcopy_for_cache to normalize values that change frequently.

    Args:
        method_name: Name of the method being called
        args: Positional arguments to the method
        kwargs: Keyword arguments to the method

    Returns:
        A string hash that uniquely identifies this method call
    """
    # Normalize the arguments and kwargs
    normalized_args = safe_deepcopy_for_cache_key(args)
    normalized_kwargs = safe_deepcopy_for_cache_key(kwargs)

    # Create a dictionary with the normalized information
    key_dict = {"method_name": method_name, "args": normalized_args, "kwargs": normalized_kwargs}

    # Convert to a stable string representation and hash it
    key_str = json.dumps(key_dict, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def save_to_cache(cache_file: Path, key: str, value: Any) -> None:
    """
    Save a value to the cache file using the given key.

    Args:
        cache_file: Path to the cache file
        key: The cache key
        value: The value to cache (will be deep-copied to ensure it's pickable)
    """
    # Create parent directories if they don't exist
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing cache
    cache = {}
    if cache_file.exists():
        try:
            with open(cache_file, "rb") as f:
                cache = pickle.load(f)
        except (pickle.PickleError, EOFError):
            # If the file is corrupted, start with an empty cache
            cache = {}

    # Make a safe copy of the value and add it to the cache
    safe_value = safe_deepcopy(value)
    cache[key] = safe_value
    logger.debug("Cache updated: %s -> %r", key, safe_value)

    # Save the updated cache
    with open(cache_file, "wb") as f:
        pickle.dump(cache, f)


def get_from_cache(cache_file: Path, key: str) -> Any:
    """
    Retrieve a value from the cache file using the given key.

    Args:
        cache_file: Path to the cache file
        key: The cache key

    Returns:
        The cached value

    Raises:
        CacheKeyError: If the key is not found in the cache
    """
    if not cache_file.exists():
        raise CacheKeyError(f"Cache file {cache_file} does not exist")
    try:
        with open(cache_file, "rb") as f:
            cache = pickle.load(f)
    except (pickle.PickleError, EOFError) as e:
        raise CacheKeyError(f"Cache file {cache_file} is corrupted") from e
    if key not in cache:
        raise CacheKeyError(f"Key {key} not found in cache")
    return cache[key]


def request_cache(fn, cache_file: Path, learn=False):
    """
    model_request_cache_wrapper for async method calls that uses a cache.

    In learn=False mode:
    - Tries to answer from cached value
    - If the cached value does not exist, raises an exception

    In learn=True mode:
    - Tries to answer from cached value
    - If the cached value does not exist, invokes the real function and adds the result to cache

    Args:
        fn: The async function to wrap
        cache_file: Path to the cache file
        learn: Whether to learn new responses (True) or only use cached ones (False)
    """

    @functools.wraps(fn)
    async def model_request_cache_wrapper(*args, **kwargs):
        # Generate a unique cache key for this request
        cache_key = generate_cache_key(fn.__name__, args, kwargs)
        try:
            # Try to get the result from cache
            result = get_from_cache(cache_file, cache_key)
            logger.debug("Cache hit for %s with key %s", fn.__name__, cache_key)
            return result
        except CacheKeyError as e:
            # If not in cache and learn=False, raise an exception
            if not learn:
                raise CacheKeyError(f"No cached response for {fn.__name__} with key {cache_key} and learn=False") from e
            # If learn=True, invoke the original method
            result = await fn(*args, **kwargs)
            # Save the result to cache
            save_to_cache(cache_file, cache_key, result)
            return result

    return model_request_cache_wrapper


def request_stream_cache(fn, cache_file: Path, learn=False):
    """
    model_request_cache_wrapper for async streaming method calls that uses a cache.

    Similar to request_cache, but handles streaming responses by caching all items
    and then replaying them when retrieved from cache.

    Args:
        fn: The async context manager function to wrap
        cache_file: Path to the cache file
        learn: Whether to learn new responses (True) or only use cached ones (False)
    """

    @functools.wraps(fn)
    @asynccontextmanager
    async def model_request_stream_cache_wrapper(*args, **kwargs):
        # Generate a unique cache key for this request
        cache_key = generate_cache_key(fn.__name__, args, kwargs)

        try:
            # Try to get the cached items
            cached_items = get_from_cache(cache_file, cache_key)

            # Define a generator that yields the cached items
            async def cached_gen():
                for item in cached_items:
                    yield item

            yield cached_gen()

        except CacheKeyError as e:
            # If not in cache and learn=False, raise an exception
            if not learn:
                raise CacheKeyError(f"No cached stream for {fn.__name__} with key {cache_key} and learn=False") from e

            # If learn=True, invoke the original method
            async with fn(*args, **kwargs) as stream:
                # Collect all items to save to cache
                all_items = []

                async def gen():
                    item_num = 0
                    async for item in stream:
                        all_items.append(item)
                        item_num += 1
                        yield item

                # Yield the generator
                gen_instance = gen()
                yield gen_instance

                # After the context manager exits, save all items to cache
                # We need to make sure all items have been consumed
                try:
                    async for _ in gen_instance:
                        pass
                except StopAsyncIteration:
                    pass

                # Save the collected items to cache
                save_to_cache(cache_file, cache_key, all_items)

    return model_request_stream_cache_wrapper


def model_patch_cache(model, cache_file: Path, learn=False):
    """Patch model with methods for caching requests and responses"""
    logger.debug("Using cache file: %s", cache_file)
    return model_patch(
        model,
        request_method=request_cache(get_request_fn(model), cache_file, learn),
        request_stream_method=request_stream_cache(get_request_stream_fn(model), cache_file, learn),
    )
