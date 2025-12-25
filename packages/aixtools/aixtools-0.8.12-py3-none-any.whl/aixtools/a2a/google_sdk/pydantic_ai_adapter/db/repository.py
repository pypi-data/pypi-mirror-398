"""Repository for storing and retrieving Pydantic AI messages."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.orm import selectinload

from aixtools.a2a.google_sdk.pydantic_ai_adapter.db.models import PydanticAIMessage
from aixtools.logging.logging_config import get_logger

logger = get_logger(__name__)


class PydanticAiMessageRepository:
    """Repository for storing/retrieving Pydantic AI messages in the database."""

    def __init__(self, engine: AsyncEngine):
        self._session_maker = async_sessionmaker(engine)

    async def get_messages_by_task(self, task_id: str):
        """Retrieves Pydantic AI messages by task ID."""
        async with self._session_maker() as session:
            stmt = (
                select(PydanticAIMessage)
                .options(selectinload(PydanticAIMessage.task))
                .where(PydanticAIMessage.task_id == task_id)
                .order_by(PydanticAIMessage.timestamp)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def store(self, messages: list[PydanticAIMessage]) -> None:
        """Stores Pydantic AI messages in the database."""
        if not messages:
            return None

        try:
            async with self._session_maker.begin() as session:
                session.add_all(messages)
        except Exception as e:
            logger.error("Failed to store Pydantic AI messages: %s", e)
            raise e
