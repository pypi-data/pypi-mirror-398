"""Convert Pydantic-AI Nodes to Markdown format."""

from abc import ABC


class NodesToMessage(ABC):  # pylint: disable=too-few-public-methods
    """
    Convert Pydantic-AI Nodes to Message format
    """

    def __init__(
        self,
        user_prompt_node: bool = True,
        user_prompt_part: bool = True,
        system_prompt_part: bool = True,
    ):
        """
        Initialize the NodeToMessage converter.
        Args:
            user_prompt_node: Whether to include UserPromptNode content
            user_prompt_part: Whether to include UserPromptPart content
            system_prompt_part: Whether to include SystemPromptPart content
        """
        self.user_prompt_node = user_prompt_node
        self.user_prompt_part = user_prompt_part
        self.system_prompt_part = system_prompt_part

    def to_str(self, nodes) -> str | None:
        """Convert a node to its string representation."""
        raise NotImplementedError("to_str method must be implemented by subclasses")
