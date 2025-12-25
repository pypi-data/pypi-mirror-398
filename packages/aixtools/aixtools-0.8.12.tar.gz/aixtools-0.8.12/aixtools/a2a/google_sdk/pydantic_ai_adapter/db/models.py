"""Database models for Pydantic AI adapter."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aixtools.a2a.google_sdk.store.models import BaseModel, TaskModel


class PydanticAIMessage(BaseModel):  # pylint: disable=too-few-public-methods
    """Model for storing Pydantic AI messages in the database."""

    __tablename__ = "pydantic_ai_messages"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.timezone("UTC", func.now()),  # pylint: disable=not-callable
        index=True,
        nullable=False,
    )

    task: Mapped["TaskModel"] = relationship("TaskModel")
