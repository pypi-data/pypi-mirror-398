"""MCP server utilities with caching and robust error handling."""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import anyio
from cachebox import TTLCache
from fastmcp.client.logging import LogMessage
from mcp import types as mcp_types
from mcp.client import streamable_http
from pydantic_ai import RunContext, exceptions
from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP, ToolResult
from pydantic_ai.toolsets.abstract import ToolsetTool

from aixtools.context import SessionIdTuple
from aixtools.logging.logging_config import get_logger
from aixtools.server.utils import create_session_headers
from aixtools.utils.config import MCP_TOOLS_MAX_RETRIES

MCP_TOOL_CACHE_TTL = 300  # 5 minutes
DEFAULT_MCP_CONNECTION_TIMEOUT = 30
DEFAULT_MCP_READ_TIMEOUT = float(60 * 5)  # 5 minutes
CACHE_KEY = "TOOL_LIST"

logger = get_logger(__name__)

# Default log_handler for MCP clients
LOGGING_LEVEL_MAP = logging.getLevelNamesMapping()


async def default_mcp_log_handler(message: LogMessage):
    """
    Handles incoming logs from the MCP server and forwards them
    to the standard Python logging system.
    """
    msg = message.data.get("msg")
    extra = message.data.get("extra")

    # Convert the MCP log level to a Python log level
    level = LOGGING_LEVEL_MAP.get(message.level.upper(), logging.INFO)

    # Log the message using the standard logging library
    logger.log(level, msg, extra=extra)


@dataclass
class MCPConfig:
    """Configuration for an MCP server retrieved from config.yaml"""

    url: str
    read_timeout: float = field(default=DEFAULT_MCP_READ_TIMEOUT)
    capabilities: dict[str, any] | None = field(default=None)


def get_mcp_client(
    url: str | None = None,
    command: str | None = None,
    args: list[str] | None = None,
    log_handler: callable = default_mcp_log_handler,  # type: ignore
) -> MCPServerStreamableHTTP | MCPServerStdio:
    """
    Create an MCP client instance based on the provided URL or command.
    By providing a log_handler, incoming logs from the MCP server can be shown, which improves debugging.

    Args:
        url (str | None): The URL of the MCP server.
        command (str | None): The command to start a local MCP server (STDIO MCP).
        args (list[str] | None): Additional arguments for the command (STDIO MCP).
    """
    if args is None:
        args = []
    if url:
        return MCPServerStreamableHTTP(url=url, log_handler=log_handler)
    if command:
        return MCPServerStdio(command=command, args=args, log_handler=log_handler)
    raise ValueError("Either url or command must be provided to create MCP client.")


def get_mcp_servers(
    mcp_configs: list[MCPConfig],
    session_id_tuple: SessionIdTuple,
    auth_token: str = None,
    max_retries: int = MCP_TOOLS_MAX_RETRIES,
    *,
    timeout: float = DEFAULT_MCP_CONNECTION_TIMEOUT,
):
    """
    Create cached MCP server instances with robust error handling and isolation.

    This function creates and returns a list of `CachedMCPServerStreamableHTTP` instances
    based on the provided URLs. Each server instance includes:
    - TTL-based caching for tool lists (5 minutes default)
    - Complete task isolation to prevent cancellation propagation
    - Comprehensive error handling and fallback mechanisms
    - Optional user/session headers for request authentication

    Args:
        mcp_configs (list[MCPConfig]): A list of MCP server configurations to use.
        session_id_tuple (SessionIdTuple): A tuple containing (user_id, session_id).
        auth_token (str, optional): The authentication token for the user. Defaults to None.
        timeout (float, optional): Timeout in seconds for MCP server connections.
    Returns:
        list[CachedMCPServerStreamableHTTP]: List of cached MCP server instances with
                                            isolation and error handling. Each server
                                            operates independently - failures in one
                                            server won't affect others.
    """
    headers = create_session_headers(session_id_tuple, auth_token)
    servers = []
    for config in mcp_configs:
        server = CachedMCPServerStreamableHTTP(
            url=config.url, headers=headers, timeout=timeout, read_timeout=config.read_timeout, max_retries=max_retries
        )
        logger.info("Using MCP server at %s", config.url)
        servers.append(server)
    return servers


def get_configured_mcp_servers(
    session_id_tuple: SessionIdTuple,
    mcp_urls: list[str],
    *,
    timeout: int = DEFAULT_MCP_CONNECTION_TIMEOUT,
    auth_token: str | None = None,
):
    """Create MCP server instances from a list of URLs."""
    return get_mcp_servers(
        [MCPConfig(url=url) for url in mcp_urls], session_id_tuple, timeout=timeout, auth_token=auth_token
    )


class CachedMCPServerStreamableHTTP(MCPServerStreamableHTTP):
    """StreamableHTTP MCP server with cachebox-based TTL caching and robust error handling.

    This class addresses the cancellation propagation issue by:
    1. Using complete task isolation to prevent CancelledError propagation
    2. Implementing comprehensive error handling for all MCP operations
    3. Using fallback mechanisms when servers become unavailable
    4. Overriding pydantic_ai methods to fix variable scoping bug
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tools_cache = TTLCache(maxsize=1, ttl=MCP_TOOL_CACHE_TTL)
        self._tools_list = None

    async def _run_direct_or_isolated(self, func, fallback, timeout: float | None):
        """Run a coroutine in complete isolation to prevent cancellation propagation.

        Args:
            func: Function that returns a coroutine to run
            fallback: Function that takes an exception and returns a fallback value
            timeout: Timeout in seconds. If None, then direct run is performed

        Returns:
            The result of the coroutine on success, or fallback value on any exception
        """
        try:
            if timeout is None:
                return await func()

            task = asyncio.create_task(func())

            # Use asyncio.wait to prevent cancellation propagation
            done, pending = await asyncio.wait([task], timeout=timeout)

            if pending:
                # Cancel pending tasks safely
                for t in pending:
                    t.cancel()
                    try:
                        await t
                    except (asyncio.CancelledError, Exception):  # pylint: disable=broad-except
                        pass
                raise TimeoutError(f"Task timed out after {timeout} seconds")

            # Get result from completed task
            completed_task = done.pop()
            if exc := completed_task.exception():
                raise exc
            return completed_task.result()

        except exceptions.ModelRetry as exc:
            logger.warning("MCP %s: %s ModelRetry: %s", self.url, func.__name__, exc)
            raise
        except TimeoutError as exc:
            logger.warning("MCP %s: %s timed out: %s", self.url, func.__name__, exc)
            return fallback(exc)
        except asyncio.CancelledError as exc:
            logger.warning("MCP %s: %s was cancelled", self.url, func.__name__)
            return fallback(exc)
        except anyio.ClosedResourceError as exc:
            logger.warning("MCP %s: %s closed resource.", self.url, func.__name__)
            return fallback(exc)
        except Exception as exc:  # pylint: disable=broad-except
            if str(exc) == "Attempted to exit cancel scope in a different task than it was entered in":
                logger.warning("MCP %s: %s enter/exit cancel scope task mismatch.", self.url, func.__name__)
            else:
                logger.warning("MCP %s: %s exception %s: %s", self.url, func.__name__, type(exc), exc)
            return fallback(exc)

    @asynccontextmanager
    async def client_streams(self):
        """Override base client_streams with wrapper logging and suppressing exceptions"""
        try:
            async with super().client_streams() as streams:  # pylint: disable=contextmanager-generator-missing-cleanup
                try:
                    yield streams
                except Exception as exc:  # pylint: disable=broad-except
                    logger.error("MCP %s: client_streams; %s: %s", self.url, type(exc).__name__, exc)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("MCP %s: client_streams: %s: %s", self.url, type(exc).__name__, exc)

    async def __aenter__(self):
        """Enter the context of the cached MCP server with complete cancellation isolation."""

        async def direct_init():
            return await super(CachedMCPServerStreamableHTTP, self).__aenter__()  # pylint: disable=super-with-arguments

        def fallback(_exc):
            self._client = None
            return self

        return await self._run_direct_or_isolated(direct_init, fallback, timeout=None)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context of the cached MCP server with complete cancellation isolation."""
        if exc_type is asyncio.CancelledError:
            logger.warning("MCP %s: __aexit__ called with cancellation - deactivating", self.url)
            self._client = None
        return await super().__aexit__(exc_type, exc_val, exc_tb)

    async def list_tools(self) -> list[mcp_types.Tool]:
        """Override to fix variable scoping bug and add caching with cancellation isolation."""
        # If client is not initialized, return empty list
        if not self._client:
            logger.warning("MCP %s: is uninitialized -> no tools", self.url)
            return []

        # First, check if we have a valid cached result
        if CACHE_KEY in self._tools_cache:
            logger.debug("Using cached tools for %s", self.url)
            return self._tools_cache[CACHE_KEY]

        # Create isolated task to prevent cancellation propagation
        async def isolated_list_tools():
            """Isolated list_tools with variable scoping bug fix."""
            result = None  # Initialize to prevent UnboundLocalError
            async with self:  # Ensure server is running
                result = await self._client.list_tools()
            if result:
                self._tools_list = result.tools or []
                self._tools_cache[CACHE_KEY] = self._tools_list
                logger.info("MCP %s: list_tools returned %d tools", self.url, len(self._tools_list))
            else:
                logger.warning("MCP %s: list_tools returned no result", self.url)
            return self._tools_list or []

        def fallback(_exc):
            return self._tools_list or []

        return await self._run_direct_or_isolated(isolated_list_tools, fallback, timeout=5.0)

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext[Any],
        tool: ToolsetTool[Any],
    ) -> ToolResult:
        """Call tool with complete isolation from cancellation using patched pydantic_ai."""
        logger.info("MCP %s: call_tool '%s' started.", self.url, name)

        # Early returns for uninitialized servers
        if not self._client:
            logger.warning("MCP %s: is uninitialized -> cannot call tool", self.url)
            return f"There was an error with calling tool '{name}': MCP connection is uninitialized."

        # Create isolated task to prevent cancellation propagation
        async def isolated_call_tool():
            """Isolated call_tool using patched pydantic_ai methods."""
            return await super(CachedMCPServerStreamableHTTP, self).call_tool(name, tool_args, ctx, tool)  # pylint: disable=super-with-arguments

        def fallback(exc):
            return f"Exception {type(exc)} when calling tool '{name}': {exc}. Consider alternative approaches."

        result = await self._run_direct_or_isolated(isolated_call_tool, fallback, timeout=3600.0)
        logger.info("MCP %s: call_tool '%s' completed.", self.url, name)
        return result


class PatchedStreamableHTTPTransport(streamable_http.StreamableHTTPTransport):
    """Patched StreamableHTTPTransport with exception suppression for _handle_post_request."""

    async def _handle_post_request(self, ctx: streamable_http.RequestContext) -> None:
        """Patched _handle_post_request with proper error handling."""
        try:
            await super()._handle_post_request(ctx)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("MCP %s: _handle_post_request %s: %s", self.url, type(exc).__name__, exc)


# Override the transport client globally
streamable_http.StreamableHTTPTransport = PatchedStreamableHTTPTransport
