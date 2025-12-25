"""
Example client implementation for Model Context Protocol (MCP) servers.
"""

import asyncio

from pydantic_ai.mcp import MCPServerSSE, MCPServerStdio

from aixtools.agents import get_agent, run_agent

USE_SEE = False


if USE_SEE:
    server = MCPServerSSE(url="http://127.0.0.1:8000/sse")
else:
    server = MCPServerStdio(command="fastmcp", args=["run", "aixtools/mcp/example_server.py"])


async def main(agent, prompt):  # pylint: disable=redefined-outer-name
    """Run an agent with MCP servers and display the result."""
    async with agent:
        ret = await run_agent(agent, prompt)
        print(f"Agent returned: {ret}")


if __name__ == "__main__":
    agent = get_agent(mcp_servers=[server])  # pylint: disable=unexpected-keyword-arg
    print(f"Agent created: {agent}")
    asyncio.run(main(agent, "What is the add of 923048502345 and 795467090123481926349123941 ?"))
