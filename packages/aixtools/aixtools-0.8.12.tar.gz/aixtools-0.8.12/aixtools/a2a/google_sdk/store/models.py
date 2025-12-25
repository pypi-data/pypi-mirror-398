"""A2A Google SDK extended models for database storage"""

from datetime import datetime

from a2a.server.models import PushNotificationConfigMixin, TaskMixin
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModel(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """Base class for a2a sdk extended models"""


class TaskModel(TaskMixin, BaseModel):  # pylint: disable=too-few-public-methods
    """A2A SDK Task model extended with created_at field"""

    __tablename__ = "tasks"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.timezone("UTC", func.now()),  # pylint: disable=not-callable
        index=True,
        nullable=False,
    )


class PushNotificationConfig(PushNotificationConfigMixin, BaseModel):  # pylint: disable=too-few-public-methods
    """A2A SDK PushNotificationConfig model extended with created_at field"""

    __tablename__ = "push_notification_configs"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.timezone("UTC", func.now()),  # pylint: disable=not-callable
        index=True,
        nullable=False,
    )
