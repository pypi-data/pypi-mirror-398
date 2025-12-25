"""
FastMCP server utilities for handling user context and threading.
"""

import asyncio
from functools import wraps

from fastmcp import Context
from fastmcp.server import dependencies

from ..context import (
    DEFAULT_SESSION_ID,
    DEFAULT_USER_ID,
    HTTP_SESSION_ID_HEADER,
    HTTP_USER_ID_HEADER,
    SessionIdTuple,
    session_id_var,
    user_id_var,
)
from ..logging.logging_config import get_logger

logger = get_logger(__name__)


def get_session_id_tuple(ctx: Context | None = None) -> SessionIdTuple:
    """
    Get the user and session IDs from the user session.
    If `ctx` is None, the current FastMCP request HTTP headers are used.
    Returns: Tuple of (user_id, session_id).
    """
    user_id = get_user_id_from_request(ctx)
    user_id = user_id or user_id_var.get(DEFAULT_USER_ID)
    session_id = get_session_id_from_request(ctx)
    session_id = session_id or session_id_var.get(DEFAULT_SESSION_ID)
    return user_id, session_id


def get_session_id_from_request(ctx: Context | None = None) -> str | None:
    """
    Get the session ID from the HTTP request headers.
    If `ctx` is None, the current FastMCP request HTTP headers are used.
    """
    try:
        return (ctx or dependencies).get_http_request().headers.get(HTTP_SESSION_ID_HEADER)
    except (ValueError, RuntimeError):
        return None


def get_user_id_from_request(ctx: Context | None = None) -> str | None:
    """
    Get the user ID from the HTTP request auth otherwise from the headers.
    Get the user ID from the HTTP request headers.
    If `ctx` is None, the current FastMCP request HTTP headers are used.
    The user_id is always returned as lowercase.

    Returns:
        str | None: The lowercase user ID, or None if not found or an error occurs.
    """
    # check if authorized user present
    try:
        user_id = (ctx or dependencies).get_http_request().user.username
        return user_id
    except (AttributeError, RuntimeError, AssertionError, ValueError):
        pass

    try:
        user_id = (ctx or dependencies).get_http_request().headers.get(HTTP_USER_ID_HEADER)
        return user_id.lower() if user_id else None
    except (ValueError, RuntimeError, AttributeError):
        return None


def get_session_id_str(ctx: Context | None = None) -> str:
    """
    Combined session ID for the current user and session.
    If `ctx` is None, the current FastMCP request HTTP headers are used.
    """
    user_id, session_id = get_session_id_tuple(ctx)
    return f"{user_id}:{session_id}"


def create_session_headers(session_id_tuple: SessionIdTuple, auth_token: str | None = None) -> dict[str, str]:
    """
    Generate headers for MCP or A2A server requests.

    This function creates a dictionary of headers to be used in requests to
    the MCP servers. If a `user_id` or `session_id` is provided, they are
    included in the headers.

    Args:
        session_id_tuple (SessionIdTuple): user_id and session_id tuple
        auth_token (str | None): Optional authorization token to include in headers

    Returns:
        dict[str, str]: A dictionary of headers for MCP server requests.
                       May be empty if no user_id, session_id, or auth_token is provided.
    """
    headers = {}
    user_id, session_id = session_id_tuple
    if auth_token:
        logger.debug("Using auth token for MCP server authentication for user:%s, session_id:%s", user_id, session_id)
        headers["Authorization"] = f"Bearer {auth_token}"
    else:
        logger.warning("No auth token found to forward to MCP/A2A servers.")

    if session_id:
        headers[HTTP_SESSION_ID_HEADER] = session_id
    if user_id:
        headers[HTTP_USER_ID_HEADER] = user_id
    return headers


def run_in_thread(func):
    """decorator to run blocking function with `asyncio.to_thread`"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper
