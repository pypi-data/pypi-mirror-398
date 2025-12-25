"""Token limit middleware and utilities for MCP servers."""
# pylint: disable=duplicate-code

import functools
import inspect
import logging
import types
from collections.abc import Awaitable
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Union, get_args, get_origin

import aiofiles
from fastmcp.server.dependencies import get_context
from fastmcp.server.middleware.middleware import Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from pydantic import TypeAdapter

from aixtools.agents.prompt import count_tokens
from aixtools.server.path import container_to_host_path
from aixtools.utils.truncation import truncate_text_head_tail

# Directory where full tool responses are saved when truncated
FULL_TOOL_RESPONSES_DIR = "/workspace/full_tool_responses"
MAX_TOOL_RETURN_TOKENS = 10000

logger = logging.Logger(__name__)


class FormatPreviewError(Exception):
    """Error when formatting a preview of truncated tool response."""


# This implementation is at parity with the way PydanticAI 1.12.0 serializes tool responses into context
_tool_return_adapter = TypeAdapter(
    Any, config={"defer_build": True, "ser_json_bytes": "base64", "val_json_bytes": "base64"}
)


def serialize_result(result: Any) -> str:
    """Serialize a result in the same way as PydanticAI"""
    try:
        return _tool_return_adapter.dump_json(result).decode()  # type: ignore
    except Exception as e:
        raise ValueError(f"Result must be serializable: {e}") from e


def get_full_tool_response_filepath() -> Path:
    """Get the filepath for saving a full tool response.

    Returns:
        Path: Container path where the full response should be saved
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"full_tool_response_{timestamp}.txt"
    return Path(FULL_TOOL_RESPONSES_DIR) / filename


async def write_response_to_workspace(content: str) -> str:
    """Write content to a file in the workspace and return the container path."""
    container_path = get_full_tool_response_filepath()

    fastmcp_ctx = get_context()
    host_path = container_to_host_path(container_path, ctx=fastmcp_ctx)

    if host_path is None:
        raise RuntimeError(f"Failed to convert container path to host path: {container_path}")

    host_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(host_path, "w", encoding="utf-8") as f:
        await f.write(content)

    return str(container_path)


def format_preview(
    content: str,
    preview_chars_start: int,
    preview_chars_end: int,
    format_preview_fn: Optional[Callable[[str], str]],
) -> str:
    """Format the full preview message with prefix and content."""
    if format_preview_fn is not None:
        try:
            preview_content = format_preview_fn(content)
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise FormatPreviewError(f"Error in custom format_preview_fn: {e}") from e
    else:
        preview_content, _ = truncate_text_head_tail(content, preview_chars_start, preview_chars_end)

    return (
        f"Tool call response exceeded max tokens for context; full response saved to {FULL_TOOL_RESPONSES_DIR} "
        "instead.\n Do not attempt to read the whole response from the file but instead use the tools available"
        "to you to search for relevant content within the file.\n"
        "Response preview:\n\n"
        f"{preview_content}"
    )


async def _process_raw_result(
    result: Any,
    max_tokens: int,
    preview_chars_start: int,
    preview_chars_end: int,
    format_preview_fn: Optional[Callable[[str], str]],
) -> Any:
    """Process a raw result and truncate if it exceeds max_tokens.

    Args:
        result: The raw result to process (can be any serializable type)
        max_tokens: Maximum number of tokens allowed before truncation
        preview_chars_start: Number of characters to show from the beginning
        preview_chars_end: Number of characters to show from the end
        format_preview_fn: Optional custom preview formatting function

    Returns:
        The original result or a truncated preview string
    """
    result_str = serialize_result(result)

    token_count = count_tokens(result_str)

    if token_count <= max_tokens:
        return result

    # Write full result to file
    try:
        await write_response_to_workspace(result_str)
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise RuntimeError(
            f"Tool response exceeded {max_tokens} tokens but failed to write to file: {e}\n\n{result_str[:1000]}..."
        ) from e

    # Return preview string
    return format_preview(result_str, preview_chars_start, preview_chars_end, format_preview_fn)


def limit_response(
    max_tokens: int = MAX_TOOL_RETURN_TOKENS,
    preview_chars_start: int = 2000,
    preview_chars_end: int = 2000,
    format_preview_fn: Optional[Callable[[str], str]] = None,
) -> Callable:
    """Decorator to automatically truncate long tool responses and save them to files.

    When a tool response exceeds max_tokens, the full response is written to a fil
    in the workspace and a truncated preview is returned instead.

    Args:
        max_tokens: Maximum number of tokens allowed in a tool response before truncation.
        preview_chars_start: Number of characters to show from the beginning of the content.
        preview_chars_end: Number of characters to show from the end of the content.
        format_preview_fn: Optional function for custom preview formatting. Takes the content string
            and returns a preview string. If passed will overwrite the default behavior.

    Warning: Converts synchronous return types into coroutines that must be awaited.
    Warning: Will convert the response to a string when truncating.

    Usage:
        @limit_response(max_tokens=1000)
        def my_tool():
            return "Very long response..."
    """

    def decorator(func: Callable) -> Callable[..., Awaitable[Any]]:
        sig = inspect.signature(func)
        return_annotation = sig.return_annotation
        is_str_type = False

        if return_annotation != inspect.Signature.empty:
            if return_annotation is str:
                is_str_type = True
            elif get_origin(return_annotation) in (types.UnionType, Union):
                args = get_args(return_annotation)
                is_str_type = str in args

            if not is_str_type:
                logger.warning(  # pylint: disable=logging-fstring-interpolation
                    f"Function '{func.__name__}' is decorated with @limit_response but has a non-str return type "
                    f"annotation: {return_annotation}. The decorator will serialize non-str returns to string, "
                    "which may not be the desired behavior. Consider annotating the return type as 'str' or "
                    "handling truncation explicitly in the function."
                )

        is_coroutine_func = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if is_coroutine_func:
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            if not is_str_type and not isinstance(result, str):
                logger.warning(
                    "Non string tool return serialized to string unexpectedly by limit_response!\n"
                    "Consider adding logic to truncate large return values for this function"
                )
            return await _process_raw_result(
                result, max_tokens, preview_chars_start, preview_chars_end, format_preview_fn
            )

        return wrapper

    return decorator


class TokenLimitMiddleware(Middleware):
    """Middleware to limit tool response size by writing large responses to files.

    When a tool response exceeds max_tokens, the full response is written
    to a file in the workspace and a truncated preview is returned instead.

    WARNING: Never apply this middleware to the file edit MCP, as we want the LLM to
    use the windowed file read and regex search from the file edit MCP to extract the
    relevant information without loading the full response into context.

    Args:
        max_tokens: Maximum number of tokens allowed in a tool response before
            truncation. Defaults to MAX_TOOL_RETURN_TOKENS
        preview_chars_start: Number of characters to show from the beginning
            of the content in the default preview. Defaults to 2000.
        preview_chars_end: Number of characters to show from the end of the
            content in the default preview. Defaults to 2000.
        format_preview_fn: Optional function for custom preview formatting. If passed will
            overwrite the default behavior for truncating tool output.
    """

    def __init__(
        self,
        max_tokens: int = MAX_TOOL_RETURN_TOKENS,
        preview_chars_start: int = 2000,
        preview_chars_end: int = 2000,
        format_preview_fn: Optional[Callable[[str], str]] = None,
    ):
        self.max_tokens = max_tokens
        self.preview_chars_start = preview_chars_start
        self.preview_chars_end = preview_chars_end
        self.format_preview_fn = format_preview_fn

    async def on_call_tool(self, context: MiddlewareContext, call_next) -> ToolResult:
        """Process tool response and limit size if needed."""
        result: ToolResult = await call_next(context)

        # Convert ToolResult to MCP result format for serialization
        mcp_result = result.to_mcp_result()
        content = mcp_result[0] if isinstance(mcp_result, tuple) else mcp_result
        result_str = serialize_result(content)

        token_count = count_tokens(result_str)

        if token_count <= self.max_tokens:
            return result

        # Write full result to file
        try:
            await write_response_to_workspace(result_str)
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise RuntimeError(
                f"Tool response exceeded {self.max_tokens} tokens but failed to write to file: "
                f"{e}\n\n{result_str[:1000]}..."
            ) from e

        # Replace content with preview
        for item in result.content:
            if isinstance(item, TextContent):
                preview_text = format_preview(
                    item.text, self.preview_chars_start, self.preview_chars_end, self.format_preview_fn
                )
                item.text = preview_text
                break

        return result
