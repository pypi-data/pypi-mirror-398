"""
This module provides functionality to save objects to a log file using pickle.
It includes a function to check if an object is pickleable and a function to perform a safe deepcopy of objects.
It also includes a function to save the objects to a log file with a timestamp.
"""

import logging
import pickle
import traceback
from copy import copy
from datetime import datetime
from pathlib import Path
from types import NoneType
from typing import Mapping, Sequence, Union

import rich

from aixtools.logging.logging_config import get_logger
from aixtools.utils.config import LOG_LEVEL, LOGS_DIR

logger = get_logger(__name__)

_is_pickleable_cache = {}


class ExceptionWrapper:  # pylint: disable=too-few-public-methods
    """
    A wrapper for exceptions to make them pickleable.
    It stores the exception type and message.
    """

    def __init__(self, exception):
        self.exc_type = str(type(exception))
        self.exc_value = str(exception)
        self.exc_traceback = traceback.format_exc()

    def __str__(self):
        return f"{self.exc_type}: {self.exc_value}\n{self.exc_traceback}"


def is_pickleable(obj, use_cache: bool = False):
    """
    Check if an object is pickleable.

    use_cache: If True, use the cache to store results of previous checks.
               Why? Some complex objects may have lists of multiple types
               inside, so whether an object is pickleable may depend on its contents.
    """
    obj_type = type(obj)
    module_name = getattr(obj_type, "__module__", "")

    # FastMCP json_schema_to_type changes __module__ which causes pickle error but for some reason goes to the cache
    if module_name == "fastmcp.utilities.json_schema_type":
        return False

    if not use_cache or obj_type not in _is_pickleable_cache:
        try:
            pickle.loads(pickle.dumps(obj))
            _is_pickleable_cache[obj_type] = True
        except Exception:  # pylint: disable=broad-exception-caught
            _is_pickleable_cache[obj_type] = False
    return _is_pickleable_cache[obj_type]


def load_from_log(log_file: Path):
    """
    Load objects from a log file.
    It reads the file in binary mode and uses pickle to deserialize the objects.
    Returns a list of objects.
    """
    objects = []
    with open(log_file, "rb") as f:
        while True:
            try:
                obj = pickle.load(f)
                objects.append(obj)
            except EOFError:
                break
    return objects


def safe_deepcopy(obj, use_cache: bool = False):
    """
    A safe deepcopy function that handles unpickleable objects.
    It uses 'is_pickleable' to check if the object is serializable and
    performs a shallow copy for unpickleable objects.

    Note: If the object is complex (e.g. has a list or dict of varying objects), using the
    cache may lead to bad results.
    For example you analyze an object with an empty list first, then another object which is non-pickable
    is added, but you use the cache result, resulting in the wrong assumption that the object is pickleable
    So by default the cache is disabled.
    """
    if isinstance(obj, Exception):
        # Wrap exceptions to make them pickleable
        obj = ExceptionWrapper(obj)

    if is_pickleable(obj, use_cache=use_cache):
        return pickle.loads(pickle.dumps(obj))  # Fast path

    if isinstance(obj, Mapping):
        return {
            k: safe_deepcopy(v, use_cache=use_cache) for k, v in obj.items() if is_pickleable(k, use_cache=use_cache)
        }

    if isinstance(obj, Sequence) and not isinstance(obj, str):
        return [safe_deepcopy(item, use_cache=use_cache) for item in obj]

    if hasattr(obj, "__dict__"):
        copy_obj = copy(obj)
        for attr, value in vars(obj).items():
            if is_pickleable(value, use_cache=use_cache):
                setattr(copy_obj, attr, value)
            else:
                setattr(copy_obj, attr, safe_deepcopy(value, use_cache=use_cache))
        return copy_obj

    return None  # fallback for non-serializable, non-introspectable objects


async def save_objects_to_logfile(objects: list, log_dir=LOGS_DIR):
    """Save the objects to a (pickle) log file"""
    with ObjectLogger(log_dir=log_dir) as object_logger:
        for obj in objects:
            await object_logger.log(obj)


class BaseLogger:
    """
    Base class for loggers.
    A context manager for logging objects.
    """

    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        pass

    async def log(self, obj):
        """Log an object to the configured destination."""

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ObjectLogger(BaseLogger):
    """
    A context manager for logging objects to a file.
    It uses pickle to save the objects and handles exceptions during the save process.
    """

    def __init__(
        self,
        log_dir=LOGS_DIR,
        verbose: bool = True,
        debug: bool | None = None,
        parent_logger: Union["BaseLogger", NoneType] = None,
    ):
        self.verbose = verbose
        self.debug = (
            debug if debug is not None else (LOG_LEVEL == logging.DEBUG)
        )  # Use the debug level from the config if not provided
        self.log_dir = log_dir
        self.file = None
        self.parent_logger = parent_logger
        self.init_log_file()

    def has_parent(self):
        """
        Check if the logger has a parent.
        If it does, it will not create a new log file.
        """
        return self.parent_logger is not None

    def init_log_file(self):
        """Initialize log file for recording agent operations."""
        if self.has_parent():
            # Do nothing: Delegates to the logger
            return
        # Create log file name
        self.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"agent_run.{timestamp}.pkl"
        logger.info("Logging to %s", self.log_file)

    def __enter__(self):
        if self.has_parent():
            # Do nothing: Delegates to the logger
            return self
        self.file = open(self.log_file, "ab")  # append in binary mode
        return self

    async def log(self, obj):
        """
        Log an object to the file.
        It uses safe_deepcopy to ensure the object is pickleable.
        """
        if self.has_parent():
            # Delegate to the parent logger
            await self.parent_logger.log(obj)
        else:
            try:
                if self.debug:
                    rich.print(obj, flush=True)
                elif self.verbose:
                    print(obj, flush=True)
                obj_to_save = safe_deepcopy(obj)
                if self.file is not None:
                    pickle.dump(obj_to_save, self.file)
                    self.file.flush()  # ensure it's written immediately
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to log object: %s", e)
                logger.error(traceback.format_exc())

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.has_parent():
            # Do nothing: Delegates to the logger
            pass
        elif self.file:
            self.file.close()


class PrintObjectLogger(BaseLogger):
    """
    Print to stdout
    """

    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        pass

    async def log(self, obj):
        """Log an object using rich print for formatted output."""
        rich.print(obj, flush=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
