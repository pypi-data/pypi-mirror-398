"""
FastMCP logging implementation for Model Context Protocol.
"""

import sys

import mcp
from fastmcp import FastMCP
from fastmcp.server.middleware import MiddlewareContext


class FastMcpLog(FastMCP):
    """A FastMCP with hooks for logging."""

    async def _call_tool(self, context: MiddlewareContext[mcp.types.CallToolRequestParams]):
        print(f"Calling tool with context: {context}", file=sys.stderr)
        ret = await super()._call_tool(context)
        print(f"Tool returned: {ret}", file=sys.stderr)
        return ret

    async def _read_resource(self, context: MiddlewareContext[mcp.types.ReadResourceRequestParams]):
        print(f"Reading resource: {context.message.uri}", file=sys.stderr)
        ret = await super()._read_resource(context)
        print(f"Resource contents: {ret}", file=sys.stderr)
        return ret

    async def get_prompt(self, key: str):
        print(f"Getting prompt: {key} ", file=sys.stderr)
        ret = await super().get_prompt(key)
        print(f"Prompt result: {ret}", file=sys.stderr)
        return ret
