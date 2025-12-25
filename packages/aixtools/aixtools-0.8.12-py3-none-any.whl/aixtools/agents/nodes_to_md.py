"""Convert Pydantic-AI Nodes to Markdown format."""

from pydantic_ai import CallToolsNode, ModelRequestNode, UserPromptNode
from pydantic_ai.messages import (
    RetryPromptPart,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_graph.nodes import End

from aixtools.agents.nodes_to_message import NodesToMessage
from aixtools.utils.utils import is_multiline, is_too_long, to_json_pretty_print

MAX_TITLE_LENGTH = 30


class NodesToMarkdown(NodesToMessage):
    """
    Convert Pydantic-AI Nodes to Markdown
    """

    def __init__(
        self,
        user_prompt_node: bool = True,
        user_prompt_part: bool = True,
        system_prompt_part: bool = True,
        title_max_length: int = MAX_TITLE_LENGTH,
    ):
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
        self.title_max_length = title_max_length

    def to_str(self, nodes) -> str | None:
        """Convert a node to its markdown string representation."""
        _, title, md = self.to_markdown(nodes)
        return f"# {title}\n\n{md}"

    def to_markdown(self, node) -> tuple[str | None, str | None, str | None]:
        """
        Get a name, title, and markdown representation of a node.

        Returns:
            name: A short name for the node
            title: A title for the node
            node_md: A markdown representation of the node or None

        Note: all values can be None if the node should not be converted (e.g., user prompt disabled).
        """
        node_md = self.node2md(node)
        if node_md is None:
            return None, None, None
        name = self.node2name(node)
        title = self.node2title(node)
        return name, title, node_md

    def _format_prompt_part(self, label: str, content: str, enabled: bool) -> str | None:
        """Format UserPromptPart or SystemPromptPart with multiline handling."""
        if not enabled:
            return None
        if is_multiline(content):  # type: ignore
            return f"### {label}\n{content}\n"
        return f"{label}: {content}\n"

    def _part2md(self, p) -> str | None:  # noqa: PLR0911  # pylint: disable=too-many-return-statements
        """Convert a Part to a string representation."""
        match p:
            case ToolCallPart():
                return f"### Tool `{p.tool_name}`\n```json\n{to_json_pretty_print(p.args)}\n```\n"
            case TextPart():
                return f"### Text\n{p.content}\n" if is_multiline(p.content) else f"{p.content}\n"
            case ToolReturnPart():
                if is_multiline(p.content) or is_too_long(p.content):
                    return f"### Tool return `{p.tool_name}`\n```json\n{to_json_pretty_print(p.content)}\n```\n"
                return f"Tool return `{p.tool_name}`: `{p.content}`"
            case UserPromptPart():
                return self._format_prompt_part("UserPromptPart", p.content, self.user_prompt_part)  # type: ignore
            case SystemPromptPart():
                return self._format_prompt_part("SystemPromptPart", p.content, self.system_prompt_part)  # type: ignore
            case RetryPromptPart():
                return f"### RetryPromptPart `{p.tool_name}`\n{p.content}\n"
            case _:
                return f"### Part {type(p)}\n{p}"

    def _part2title(self, p) -> str:  # noqa: PLR0911  # pylint: disable=too-many-return-statements
        """Convert a Part to a title representation."""
        match p:
            case ToolCallPart():
                return f"Tool `{p.tool_name}`"
            case TextPart():
                return self._to_title_length(p.content)
            case ToolReturnPart():
                return f"Tool return `{p.tool_name}`"
            case UserPromptPart():
                return f"UserPromptPart: {self._to_title_length(p.content)}\n"
            case SystemPromptPart():
                return f"SystemPromptPart: {self._to_title_length(p.content)}\n"
            case RetryPromptPart():
                return f"WARNING: Retry {p.tool_name}"
            case _:
                return f"{type(p)}: {self._to_title_length(p)}"

    def _parts2md(self, parts) -> str | None:
        """Convert to string a list of Parts with a given prefix."""
        if len(parts) == 0:
            return None

        if len(parts) == 1:
            s = self._part2md(parts[0])
            if s is None:
                return None
            return s + "\n"

        result = ""
        for p in parts:
            s = self._part2md(p)
            if s is not None:
                result += s + "\n"
        return result

    def _parts2title(self, parts) -> str:
        """Convert to title a list of Parts with a given prefix."""
        if len(parts) == 0:
            return ""

        if len(parts) == 1:
            return self._part2title(parts[0])

        result = ""
        for p in parts:
            s = self._part2title(p)
            # Prefer 'Tool' titles
            if s.startswith("ERROR"):
                return s
            if s.startswith("Tool"):
                return s
            if not result:
                result = s

        return result

    def node2md(self, n) -> str | None:
        """Convert a node in a markdown format"""
        match n:
            case UserPromptNode():
                return f"# UserPrompt\n{n.user_prompt}\n" if self.user_prompt_node else None
            case CallToolsNode():
                return f"# Call tools\n{self._parts2md(n.model_response.parts)}\n"
            case ModelRequestNode():
                return f"# Model request\n{self._parts2md(n.request.parts)}\n"
            case End():
                return f"# End\n{n.data.output}\n"
            case RetryPromptPart():
                return "# Retry tool"
            case _:
                return f"{type(n)}: {n}"

    def node2title(self, n) -> str | None:
        """Get a title for a node."""
        match n:
            case UserPromptNode():
                return self._to_title_length(n.user_prompt)
            case CallToolsNode():
                return self._parts2title(n.model_response.parts)
            case ModelRequestNode():
                return self._parts2title(n.request.parts)
            case End():
                return self._to_title_length(n.data.output)
            case _:
                return f"{type(n)}: {n}"

    def node2name(self, n) -> str | None:
        """Get a short name for a node."""
        match n:
            case UserPromptNode():
                return "UserPrompt"
            case CallToolsNode():
                return "Call tools"
            case ModelRequestNode():
                return "Model request"
            case End():
                return "End"
            case _:
                return f"{type(n)}: {n}"

    def _to_title_length(self, s) -> str:
        """Truncate a string to a maximum length for title display."""
        s = str(s).replace("\n", " ").strip()
        return s[: self.title_max_length] + "..." if len(s) > self.title_max_length else s
