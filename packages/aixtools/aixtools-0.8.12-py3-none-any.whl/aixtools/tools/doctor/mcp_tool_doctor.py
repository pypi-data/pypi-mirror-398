import argparse
import asyncio

from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP

from aixtools.agents import get_agent, run_agent
from aixtools.tools.doctor.tool_doctor import TOOL_DOCTOR_PROMPT
from aixtools.tools.doctor.tool_recommendation import ToolRecommendation


async def tool_doctor_mcp(
    mcp_url: str = "http://127.0.0.1:8000/mcp",
    mcp_server: MCPServerStreamableHTTP | MCPServerStdio | None = None,
    verbose: bool = False,
    debug: bool = False,
) -> list[ToolRecommendation]:
    """
    Run the tool doctor agent to analyze tools from an MCP server and give recommendations.

    Usage examples:
        # Using an http MCP server
        ret = await tool_doctor_mcp(mcp_url='http://127.0.0.1:8000/mcp')
        print(ret)

        # Using a stdio MCP server
        server = MCPServerStdio(command='fastmcp', args=['run', 'my_mcp_server.py'])
        ret = await tool_doctor_mcp(mcp_server=server)
        print(ret)
    """
    if mcp_server is None:
        mcp_server = MCPServerStreamableHTTP(url=mcp_url)
    agent = get_agent(toolsets=[mcp_server], output_type=list[ToolRecommendation])
    async with agent:
        ret, nodes = await run_agent(agent, TOOL_DOCTOR_PROMPT, verbose=verbose, debug=debug)
    return ret  # type: ignore


def main_cli():
    """Command line interface for tool doctor MCP."""
    parser = argparse.ArgumentParser(description="Analyze tools from an MCP server and provide recommendations")

    # MCP server connection options
    server_group = parser.add_mutually_exclusive_group()
    server_group.add_argument(
        "--mcp-url",
        default="http://127.0.0.1:8000/mcp",
        help="URL of the HTTP MCP server (default: http://127.0.0.1:8000/mcp)",
    )
    server_group.add_argument("--stdio-command", help="Command to run STDIO MCP server (e.g., 'fastmcp')")

    parser.add_argument(
        "--stdio-args",
        nargs="*",
        default=[],
        help="Arguments for STDIO MCP server command (e.g., 'run', 'my_server.py')",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    async def run():
        mcp_server = None
        if args.stdio_command:
            mcp_server = MCPServerStdio(command=args.stdio_command, args=args.stdio_args)
            recommendations = await tool_doctor_mcp(mcp_server=mcp_server, verbose=args.verbose, debug=args.debug)
        else:
            recommendations = await tool_doctor_mcp(mcp_url=args.mcp_url, verbose=args.verbose, debug=args.debug)

        print("Tool Doctor Recommendations:")
        print("=" * 50)
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")

    asyncio.run(run())


if __name__ == "__main__":
    main_cli()
