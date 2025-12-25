"""Module for managing remote agent connections and task handling using the A2A client."""

import asyncio
from typing import Callable

from a2a.client import Client
from a2a.types import (
    AgentCard,
    Message,
    Task,
    TaskIdParams,
    TaskQueryParams,
    TaskState,
)

from aixtools.logging.logging_config import get_logger

logger = get_logger(__name__)


def is_in_terminal_state(task: Task) -> bool:
    """Checks if the task is in a terminal state."""
    return task.status.state in [
        TaskState.completed,
        TaskState.canceled,
        TaskState.failed,
    ]


def is_in_terminal_or_interrupted_state(task: Task) -> bool:
    """Checks if the task is in a terminal state or requires input/unknown state."""
    return task.status.state in [
        TaskState.input_required,
        TaskState.unknown,
    ] or is_in_terminal_state(task)


class RemoteAgentConnection:
    """Represents a connection to a remote agent, allowing message sending and task management."""

    def __init__(self, card: AgentCard, client: Client):
        self._client = client
        self._card = card

    def get_agent_card(self) -> AgentCard:
        """
        Returns the agent card associated with this connection.
        """
        return self._card

    async def send_message(self, message: Message) -> Task | Message | None:
        """
        Sends a message to the remote agent and returns either a Task, a Message, or None.
        """
        last_task: Task | None = None
        try:
            async for event in self._client.send_message(message):
                if isinstance(event, Message):
                    return event
                if is_in_terminal_or_interrupted_state(event[0]):
                    return event[0]
                last_task = event[0]
        except Exception as e:
            logger.error("Exception found in send_message: %s", str(e))
            raise e
        return last_task

    async def send_message_with_polling(
        self,
        message: Message,
        *,
        sleep_time: float = 2.0,
        max_iter=1000,
        on_task_submitted: Callable[[str], None] | None = None,
    ) -> Task | Message:
        """
        Sends a message to the remote agent and polls for the task status at regular intervals.
        If the task reaches a terminal state or is interrupted, it returns the task.
        If the task does not complete within the maximum number of iterations, it raises an exception.
        """
        last_task = await self.send_message(message)
        if not last_task:
            raise ValueError("No task or message returned from send_message")
        if isinstance(last_task, Message):
            return last_task

        if on_task_submitted:
            on_task_submitted(last_task.id)

        if is_in_terminal_or_interrupted_state(last_task):
            return last_task
        task_id = last_task.id
        for _ in range(max_iter):
            await asyncio.sleep(sleep_time)
            task = await self._client.get_task(TaskQueryParams(id=task_id))
            if is_in_terminal_or_interrupted_state(task):
                return task

        timeout_seconds = max_iter * sleep_time
        raise Exception(f"Task did not complete in {timeout_seconds} seconds")  # pylint: disable=broad-exception-raised

    async def cancel_task(self, task_id: str) -> Task:
        """
        Cancels a task by its ID.
        """
        try:
            return await self._client.cancel_task(TaskIdParams(id=task_id))
        except Exception as e:
            logger.error("Exception found in cancel_task: %s", str(e))
            raise e
