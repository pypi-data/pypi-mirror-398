"""Database storage implementation for Pydantic AI agent history."""

import uuid

from pydantic_ai import ModelMessagesTypeAdapter, ModelRequest, ModelResponse
from pydantic_core import to_jsonable_python

from aixtools.a2a.google_sdk.pydantic_ai_adapter.db.models import PydanticAIMessage
from aixtools.a2a.google_sdk.pydantic_ai_adapter.db.repository import PydanticAiMessageRepository
from aixtools.a2a.google_sdk.pydantic_ai_adapter.storage import PydanticAiAgentHistoryStorage


class DatabasePydanticAiAgentHistoryStorage(PydanticAiAgentHistoryStorage):
    """Database-backed implementation of PydanticAiAgentHistoryStorage."""

    def __init__(self, repo: PydanticAiMessageRepository):
        self._repo = repo

    async def get(self, task_id: str) -> list[ModelRequest | ModelResponse] | None:
        pydantic_ai_messages = await self._repo.get_messages_by_task(task_id)
        if not pydantic_ai_messages:
            return []

        messages = [msg.content for msg in pydantic_ai_messages]
        return ModelMessagesTypeAdapter.validate_python(messages)

    async def store(self, task_id: str, messages: list[ModelRequest | ModelResponse]) -> None:
        as_python_objects = to_jsonable_python(messages, bytes_mode="base64")

        entities = [
            PydanticAIMessage(
                id=str(uuid.uuid4()),
                task_id=task_id,
                content=msg,
            )
            for msg in as_python_objects
        ]
        await self._repo.store(entities)
