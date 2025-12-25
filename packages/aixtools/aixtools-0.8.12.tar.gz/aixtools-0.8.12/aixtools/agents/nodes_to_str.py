"""Convert Pydantic-AI Nodes to String format."""

from collections.abc import Iterable

from pydantic_ai import CallToolsNode, ModelRequestNode, UserPromptNode
from pydantic_ai.messages import SystemPromptPart, TextPart, ToolCallPart, ToolReturnPart, UserPromptPart
from pydantic_graph.nodes import End

from aixtools.agents.nodes_to_message import NodesToMessage
from aixtools.utils.utils import is_multiline, tabit


def print_nodes(nodes):
    """Convert a list of nodes in a readable format."""
    n2s = NodesToString()
    print(n2s.to_str(nodes))


class NodesToString(NodesToMessage):  # pylint: disable=too-few-public-methods
    """
    Convert Pydantic-AI Nodes to String
    """

    def __init__(self, user_prompt_node: bool = True, user_prompt_part: bool = True, system_prompt_part: bool = True):
        """
        Initialize the NodeToMarkdown converter.
        Args:
            user_prompt_node: Whether to include UserPromptNode content
            user_prompt_part: Whether to include UserPromptPart content
            system_prompt_part: Whether to include SystemPromptPart content
        """
        super().__init__(
            user_prompt_node=user_prompt_node,
            user_prompt_part=user_prompt_part,
            system_prompt_part=system_prompt_part,
        )

    def _format_content(self, label: str, content: str, prefix: str) -> str:
        """Format content with optional multiline handling."""
        if is_multiline(content):
            pre = f"{prefix}\t|"
            return f"{prefix}{label}:\n{tabit(content, pre)}"
        return f"{prefix}{label}: {content}"

    def _part2str(self, p, prefix: str = "\t") -> str | None:
        """Convert a Part to a string representation."""
        match p:
            case ToolCallPart():
                return f"{prefix}Tool: {p.tool_name}, args: {p.args}"
            case TextPart():
                return self._format_content("Text", p.content, prefix)
            case ToolReturnPart():
                return f"{prefix}Tool return: {p.tool_name}, content: {p.content}"
            case UserPromptPart():
                return None if not self.user_prompt_part else self._format_content("UserPromptPart", p.content, prefix)  # type: ignore  # pylint: disable=line-too-long
            case SystemPromptPart():
                return (
                    None if not self.system_prompt_part else self._format_content("SystemPromptPart", p.content, prefix)
                )  # type: ignore
            case _:
                return f"{prefix}Part {type(p)}: {p}"

    def _parts2str(self, parts, prefix: str = "") -> str:
        """Convert to string a list of Parts with a given prefix."""
        if len(parts) == 0:
            return f"{prefix}No parts\n"

        if len(parts) == 1:
            s = self._part2str(parts[0], prefix=prefix)
            return s + "\n" if s else ""

        result = ""
        for i, p in enumerate(parts):
            s = self._part2str(p, prefix=f"{prefix}{i}: ")
            result += f"{s}\n" if s else ""
        return result

    def _node2str(self, n) -> str:
        """Convert a node in a readable format."""
        match n:
            case UserPromptNode():
                assert n.user_prompt is not None

                return (
                    f"UserPrompt:\n{tabit(n.user_prompt)}\n"
                    if n.user_prompt is not None and self.user_prompt_node
                    else ""
                )
            case CallToolsNode():
                parts_str = self._parts2str(n.model_response.parts, prefix="\t")
                return f"Call tools:\n{parts_str}\n"
            case ModelRequestNode():
                parts_str = self._parts2str(n.request.parts, prefix="\t")
                return f"Model request:\n{parts_str}\n"
            case End():
                return f"End:\n{tabit(n.data.output)}\n"
            case _:
                return f"{type(n)}: {n}"

    def to_str(self, nodes) -> str:
        """Convert a list of nodes in a readable format."""
        out = ""
        if isinstance(nodes, Iterable) and not isinstance(nodes, (str, bytes)):
            for n in nodes:
                out += self._node2str(n)
        else:
            # Assume it's a single node
            out += self._node2str(nodes)
        return out
