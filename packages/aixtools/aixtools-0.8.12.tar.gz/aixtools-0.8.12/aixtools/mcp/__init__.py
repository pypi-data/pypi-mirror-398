"""
Model Context Protocol (MCP) implementation for AI agent communication.
"""

from aixtools.mcp.capabilities import (
    CAPABILITY_END,
    CAPABILITY_START,
    build_instructions_with_capabilities,
    get_features,
    parse_capabilities,
)
from aixtools.mcp.exceptions import AixToolError
from aixtools.mcp.fast_mcp_log import FastMcpLog
from aixtools.mcp.middleware import AixErrorHandlingMiddleware, TokenLimitMiddleware
from aixtools.mcp.server import create_mcp_server, get_default_middleware

__all__ = [
    "AixErrorHandlingMiddleware",
    "AixToolError",
    "CAPABILITY_END",
    "CAPABILITY_START",
    "FastMcpLog",
    "TokenLimitMiddleware",
    "build_instructions_with_capabilities",
    "create_mcp_server",
    "get_default_middleware",
    "get_features",
    "parse_capabilities",
]
