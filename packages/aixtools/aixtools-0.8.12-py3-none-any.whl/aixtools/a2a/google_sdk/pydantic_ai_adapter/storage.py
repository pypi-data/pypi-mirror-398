"""Storage interface and in-memory implementation for Pydantic AI agent history."""

from abc import ABC, abstractmethod

from pydantic_ai.messages import ModelRequest, ModelResponse


class PydanticAiAgentHistoryStorage(ABC):
    """Interface for storing and retrieving Pydantic AI agent message history."""

    @abstractmethod
    async def get(self, task_id: str) -> list[ModelRequest | ModelResponse]:
        """Retrieve message history for a given task ID."""

    @abstractmethod
    async def store(self, task_id: str, messages: list[ModelRequest | ModelResponse]) -> None:
        """Store message history for a given task ID."""


class InMemoryHistoryStorage(PydanticAiAgentHistoryStorage):
    """In-memory implementation of PydanticAiAgentHistoryStorage for testing purposes."""

    def __init__(self):
        self.storage: dict[str, list[ModelRequest | ModelResponse]] = {}

    async def get(self, task_id: str) -> list[ModelRequest | ModelResponse]:
        return self.storage.get(task_id, [])

    async def store(self, task_id: str, messages: list[ModelRequest | ModelResponse]) -> None:
        self.storage[task_id] = messages
