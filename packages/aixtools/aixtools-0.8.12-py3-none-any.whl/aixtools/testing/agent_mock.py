"""Mock agent that replays previously recorded nodes for testing purposes."""

import pickle
from pathlib import Path
from typing import Any

from aixtools.logging.log_objects import safe_deepcopy


class AgentMock:
    """
    Mock agent that replays previously recorded nodes.
    Used for testing or replaying agent runs without executing the actual agent.

    Example:

        # Run an agent and save its nodes
        agent = get_agent(...)
        ret, nodes = await run_agent(agent, prompt, ...)

        # Use AgentMock to replay the nodes
        agent_mock = AgentMock(nodes=nodes, result_output=ret)

        # Now we can use agent_mock in place of the original agent
        ret, nodes = await run_agent(agent_mock, prompt, ...)

        # Save the mock agent to a file
        agent_mock.save(Path("agent_mock.pkl"))
    """

    def __init__(self, nodes: list[Any], result_output: str | None = None):
        """
        Initialize the mock agent with pre-recorded nodes.

        Args:
            nodes: List of nodes from a previous agent run
            result_output: Optional output to return as the final result
        """
        self.nodes = nodes
        self.result_output = result_output

    def save(self, path: Path) -> None:
        """
        Save the mock agent to a file.
        Uses safe_deepcopy to ensure nodes are serializable.

        Args:
            path: Path to save the agent mock data
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"nodes": safe_deepcopy(self.nodes, use_cache=False), "result_output": self.result_output}  # pylint: disable=unexpected-keyword-arg
        with open(path, "wb") as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path: Path) -> "AgentMock":
        """
        Load a mock agent from a file.

        Args:
            path: Path to load the agent mock data from

        Returns:
            AgentMock instance with loaded data
        """
        with open(path, "rb") as f:
            data = pickle.load(f)
        return cls(nodes=data["nodes"], result_output=data["result_output"])

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""

    def iter(self, **kwargs) -> "AgentRunMock":  # pylint: disable=unused-argument
        """
        Create an async iterator that replays the recorded nodes.

        Args:
            prompt: The prompt (ignored in mock, kept for interface compatibility)
            usage_limits: Usage limits (ignored in mock, kept for interface compatibility)

        Returns:
            An async iterator that yields the recorded nodes
        """
        return AgentRunMock(self.nodes, self.result_output)


class AgentRunMock:
    """
    Mock agent run that yields pre-recorded nodes.
    """

    def __init__(self, nodes: list[Any], result_output: str | None = None):
        """
        Initialize the mock agent run.

        Args:
            nodes: List of nodes to replay
            result_output: Optional output to return as the final result
        """
        self.nodes = nodes
        self.result = MockResult(result_output)
        self._index = 0

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""

    def __aiter__(self):
        """Return self as async iterator."""
        return self

    async def __anext__(self):
        """Yield the next node from the recorded list."""
        if self._index >= len(self.nodes):
            raise StopAsyncIteration
        node = self.nodes[self._index]
        self._index += 1
        return node


class MockResult:  # pylint: disable=too-few-public-methods
    """
    Mock result object that mimics the agent result structure.
    """

    def __init__(self, output: str | None = None):
        """
        Initialize the mock result.

        Args:
            output: The output to return
        """
        self.output = output

    def __str__(self):
        return f"MockResult(output={self.output})"
