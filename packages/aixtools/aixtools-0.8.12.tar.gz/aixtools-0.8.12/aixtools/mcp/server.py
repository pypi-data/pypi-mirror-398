"""Utilities for FastMCP servers."""

from typing import Any

from fastmcp import FastMCP
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware
from fastmcp.utilities.types import NotSet

from aixtools.auth.auth import AccessTokenAuthProvider
from aixtools.logging.logging_config import get_logger
from aixtools.mcp.middleware import AixErrorHandlingMiddleware, TokenLimitMiddleware
from aixtools.utils import config


def get_default_middleware() -> list:
    """
    Get the default middleware stack for MCP servers.

    Returns a list of middleware instances that should be used by default
    in all MCP servers. Callers can customize this list by adding or removing
    middleware as needed.

    Returns:
        List of middleware instances in order:
        1. LoggingMiddleware - Logs all requests/responses
        2. AixErrorHandlingMiddleware - Handles errors with tracebacks
        3. TokenLimitMiddleware - Truncates large tool responses
        4. TimingMiddleware - Logs timing information

    Example:
        >>> # Use default middleware
        >>> middleware = get_default_middleware()

        >>> # Exclude TokenLimitMiddleware for file edit tools
        >>> middleware = [m for m in get_default_middleware() if not isinstance(m, TokenLimitMiddleware)]

        >>> # Add custom middleware
        >>> middleware = get_default_middleware()
        >>> middleware.append(MyCustomMiddleware())
    """
    return [
        LoggingMiddleware(include_payloads=True, logger=get_logger("middleware.log")),
        AixErrorHandlingMiddleware(include_traceback=True, logger=get_logger("middleware.err")),
        TokenLimitMiddleware(),
        TimingMiddleware(logger=get_logger("middleware.timing")),
    ]


def create_mcp_server(
    *,
    name: str,
    instructions: str | None = None,
    **kwargs: Any,
) -> FastMCP:
    """
    MCP server instance with preconfigured auth and middleware.

    All FastMCP constructor parameters are supported via **kwargs.

    Args:
        name: Server name
        instructions: Optional server instructions
        **kwargs: All other FastMCP constructor parameters:
            - version: str | None
            - auth: AuthProvider | None (AccessTokenAuthProvider if not set, pass None to disable)
            - middleware: list[Middleware] | None (custom middleware if not set, pass None to disable)
            - lifespan: Callable | None
            - tool_serializer: Callable[[Any], str] | None
            - cache_expiration_seconds: float | None
            - on_duplicate_tools: DuplicateBehavior | None
            - on_duplicate_resources: DuplicateBehavior | None
            - on_duplicate_prompts: DuplicateBehavior | None
            - resource_prefix_format: Literal["protocol", "path"] | None
            - mask_error_details: bool | None
            - tools: list[Tool | Callable] | None
            - tool_transformations: dict[str, ToolTransformConfig] | None
            - dependencies: list[str] | None
            - include_tags: set[str] | None
            - exclude_tags: set[str] | None
            - include_fastmcp_meta: bool | None

    Returns:
        Configured FastMCP server instance
    """
    middleware = kwargs.pop("middleware", NotSet)
    auth = kwargs.pop("auth", NotSet)

    if middleware is NotSet:
        middleware = get_default_middleware()

    # env SKIP_MCP_AUTHORIZATION overrides config.
    if config.SKIP_MCP_AUTHORIZATION:
        auth = None
    elif auth is NotSet:
        auth = AccessTokenAuthProvider()

    mcp_args = {
        "name": name,
        "instructions": instructions,
        "auth": auth,
        "middleware": middleware,
        **kwargs,
    }

    return FastMCP(**mcp_args)
