"""
Utility functions for working with node objects.
"""

import json
import traceback

import rich
from mcp.types import CallToolResult, EmbeddedResource, ImageContent, TextContent
from pydantic_ai import CallToolsNode, ModelRequestNode, UserPromptNode
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.result import FinalResult
from pydantic_ai.usage import Usage
from pydantic_graph import End

from aixtools.logging.logging_config import get_logger
from aixtools.logging.model_patch_logging import ModelRawRequest, ModelRawRequestResult
from aixtools.utils.utils import escape_newline

logger = get_logger(__name__)

MAX_STR_LEN = 200
DEBUG = False


def has_multiple_lines(s: str) -> bool:
    """Check if a string has multiple lines."""
    return s.count("\n") > 1


def get_node_type(node):
    """Return the type name of a node as a string."""
    return str(type(node).__name__)


def extract_node_types(nodes: list) -> set[str]:
    """Extract all unique node types from a list of nodes."""
    types = set()
    for node in nodes:
        node_type = get_node_type(node)
        types.add(node_type)
    return types


def to_str(s, max_len=MAX_STR_LEN):
    """Format string content with appropriate quoting based on content structure."""
    s = str(s)
    if has_multiple_lines(s):
        s = escape_newline(s)
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def try_json(s):
    """Attempt to parse string as JSON, returning parsed object or original string."""
    # Can it be parsed as a JSON object?
    try:
        d = json.loads(s)
        return d
    except Exception:  # pylint: disable=broad-exception-caught
        pass
    return s


class NodeTitle:
    """Class to create a title for nodes in a human-readable format."""

    def __init__(self):
        pass

    def summary(self, node):  # noqa: PLR0911, PLR0912, pylint: disable=too-many-return-statements,too-many-branches
        """Generate a summary string for a node."""
        if node is None:
            return "None"
        _type = str(type(node).__name__)
        if DEBUG:
            rich.print(node)
        try:
            match node:
                case str() | bool() | float() | int():
                    return f"`{_type}`: {to_str(node)}"
                case list():
                    return to_str(f"`list` ({len(node)}):\n[" + "\n, ".join([self.summary(n) for n in node]) + "]")
                case dict():
                    return to_str(
                        f"`dict` ({len(node)}): "
                        + "{"
                        + "\n, ".join([f"{k}: {self.summary(v)}" for k, v in node.items()])
                        + "}"
                    )
                case tuple():
                    if len(node) == 0:
                        return "`tuple`: Empty"
                    items = [self.summary(n) for n in node]
                    items_str = "(" + ", ".join([str(item) for item in items]) + ")"
                    return f"`tuple` ({len(node)}): {to_str(items_str)}"
                case CallToolsNode():
                    return f"`{_type}`: {to_str(self.summary(node.model_response))}"
                case CallToolResult():
                    return f"`{_type}`: {to_str(self.summary_call_tool_result(node))}"
                case End():
                    return f"`{_type}`: {to_str(self.summary(node.data))}"
                case FinalResult():
                    if hasattr(node, "data"):
                        return f"`{_type}`: {to_str(self.summary(node.data))}"
                    if node.tool_name:
                        return f"`{_type}`: {to_str(node.tool_name)}"
                    return f"`{_type}`"
                case ModelRawRequest():
                    return f"`{_type}`: {to_str(self.summary_model_raw_request(node))}"
                case ModelRawRequestResult():
                    return f"`{_type}`: {to_str(self.summary(node.result))}"
                case ModelRequest():
                    return f"`{_type}`: {to_str(self.summary_model_request(node))}"
                case ModelRequestNode():
                    return f"`{_type}`: {to_str(self.summary(node.request))}"
                case ModelRequestParameters():
                    return f"`{_type}`: {to_str(self.summary_model_request_parameters(node))}"
                case ModelResponse():
                    return f"`{_type}`: {to_str(self.summary_model_response(node))}"
                case TextPart() | SystemPromptPart() | UserPromptPart() | ToolReturnPart() | RetryPromptPart():
                    return self.summary(node.content)
                case TextContent():
                    return self.summary(node.text)
                case ImageContent():
                    return f"Image: {node.mimeType}"
                case EmbeddedResource():
                    return f"Resource: {node.resource}"
                case UserPromptNode():
                    return f"`{_type}`: {to_str(self.summary_user_prompt(node))}"
                case ToolCallPart():
                    args = node.args
                    if isinstance(args, str):
                        args = try_json(args)
                    if isinstance(args, dict):
                        args = ", ".join([f"{k} = {self.summary(v)}" for k, v in args.items()])
                    return f"{node.tool_name}({to_str(args)})"
                case Usage():
                    return f"`{_type}`: {to_str(self.summary_usage(node))}"
                case _:
                    logger.debug("NodeSummary.summary(): Unknown node type %s", type(node))
                    return f"`{type(node)}`: {str(node)}"
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error while summarizing {_type}: {e}")
            traceback.print_exc()
            return f"`{_type}`: {to_str(to_str(node))}"

    def summary_call_tool_result(self, node: CallToolResult):
        """Generate summary for CallToolResult node by joining content summaries."""
        out = [self.summary(c) for c in node.content]
        return "\n".join(out)

    def summary_model_raw_request(self, node: ModelRawRequest):
        """Format ModelRawRequest node showing args and kwargs in readable format."""
        args = [self.summary(p) for p in node.args]
        kwargs = [f"{k}={self.summary(v)}" for k, v in node.kwargs.items()]
        out = ""
        if len(args) > 0:
            out += ", ".join(args)
        if len(kwargs) > 0:
            if len(out) > 0:
                out += ", "
            out += ", ".join([f"{k} = {self.summary(v)}" for k, v in kwargs])
        return out

    def summary_model_request(self, node: ModelRequest):
        """Generate summary for ModelRequest by joining part summaries."""
        out = [self.summary(p) for p in node.parts]
        return "\n".join(out)

    def summary_model_request_parameters(self, node: ModelRequestParameters):
        """Format model request parameters with tools and result tools."""
        out = ""

        if hasattr(node, "function_tools"):
            tools = [self.tool_description(tool_definition) for tool_definition in node.function_tools]
            if len(tools) > 0:
                if len(tools) == 1:
                    out += f"Tool: {tools[0]}"
                else:
                    out += "Tools:\n" + "\n".join(tools)

        if hasattr(node, "output_tools"):
            result_tools = [self.tool_description(tool_definition) for tool_definition in node.output_tools]
            if len(result_tools) > 0:
                if len(out) > 0:
                    out += "\n"
                out += "Output Tools:\n" + "\n".join(result_tools)

        return out if len(out) > 0 else ""

    def summary_model_response(self, node: ModelResponse):
        """Generate summary for ModelResponse by joining part summaries."""
        out = [self.summary(p) for p in node.parts]
        return "\n".join(out)

    def summary_usage(self, node: Usage):
        """Format token usage information showing request and response tokens."""
        return f"tokens: ({node.request_tokens}, {node.response_tokens}"

    def summary_user_prompt(self, node: UserPromptNode):
        """Generate summary for UserPromptNode handling both string and list formats."""
        if isinstance(node.user_prompt, str):
            return self.summary(node.user_prompt)
        if node.user_prompt:
            out = [self.summary(p) for p in node.user_prompt]
            return "\n".join(out)
        return "<empty>"

    def tool_description(self, tool_definition):
        """Format tool definition with name, description and parameters if multi-line."""
        descr = f"`{tool_definition.name}`: {self.summary(tool_definition.description)}"
        if has_multiple_lines(descr):
            args = ""
            for k, v in tool_definition.parameters_json_schema.items():
                args += f"- {k}: {v}\n"
            return f"`{tool_definition.name}`: {self.summary(tool_definition.description)}\n{args}"
        return descr
