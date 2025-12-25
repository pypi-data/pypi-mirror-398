"""Utility functions to print nodes and their parts in a readable format."""

from pydantic_ai import CallToolsNode, ModelRequestNode, UserPromptNode
from pydantic_ai.messages import TextPart, ToolCallPart
from pydantic_graph.nodes import End


def tab(s, prefix: str = "\t|") -> str:
    """ "Tab a string with a given prefix (default is tab + pipe)."""
    return prefix + str(s).replace("\n", "\n" + prefix)


def part2str(p, prefix: str = "\t"):
    """Convert a Part to a string representation."""
    match p:
        case ToolCallPart():
            return f"{prefix}Tool: {p.tool_name}, args: {p.args}"
        case TextPart():
            return f"{prefix}Text: {tab(p.content)}"
        case _:
            return f"{prefix}Part {type(p)}: {p}"


def print_parts(parts, prefix: str = ""):
    """Print a list of Parts with a given prefix."""
    if len(parts) == 0:
        print(f"{prefix}No parts")
        return
    if len(parts) == 1:
        print(part2str(parts[0], prefix=prefix))
        return
    for p in parts:
        print(f"{part2str(p, prefix=prefix)}")


def print_node(n):
    """Print a node in a readable format."""
    match n:
        case UserPromptNode():
            print(f"Prompt:\n{tab(n.user_prompt)}")
        case CallToolsNode():
            print_parts(n.model_response.parts)
        case ModelRequestNode():
            print(f"Model request: ~ {len(str(n))} chars")
        case End():
            pass  # print(f"End:\n{tab(n.data.output)}")
        case _:
            print(f"{type(n)}: {n}")


def print_nodes(nodes):
    """Print a list of nodes in a readable format."""
    for n in nodes:
        print_node(n)
