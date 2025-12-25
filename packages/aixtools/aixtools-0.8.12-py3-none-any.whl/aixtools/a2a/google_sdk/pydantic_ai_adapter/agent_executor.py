"""Agent Executor implementation using Pydantic AI agent."""

import asyncio
from pathlib import Path

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    FilePart,
    FileWithUri,
    Message,
    Part,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import get_file_parts, get_message_text, new_agent_text_message, new_task
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent
from sqlalchemy.ext.asyncio import AsyncEngine

from aixtools.a2a.google_sdk.pydantic_ai_adapter.db.repository import PydanticAiMessageRepository
from aixtools.a2a.google_sdk.pydantic_ai_adapter.db.storage import DatabasePydanticAiAgentHistoryStorage
from aixtools.a2a.google_sdk.pydantic_ai_adapter.storage import InMemoryHistoryStorage, PydanticAiAgentHistoryStorage
from aixtools.a2a.google_sdk.remote_agent_connection import is_in_terminal_state
from aixtools.a2a.google_sdk.types import AgentExecutorFactory
from aixtools.a2a.google_sdk.utils import get_session_id_tuple
from aixtools.agents import get_agent
from aixtools.agents.prompt import build_user_input
from aixtools.context import SessionIdTuple, auth_token_var
from aixtools.logging.logging_config import get_logger
from aixtools.mcp.client import get_configured_mcp_servers

logger = get_logger(__name__)


class AgentParameters(BaseModel):
    """Parameters for configuring the Pydantic AI agent."""

    system_prompt: str
    mcp_servers: list[str]


class RunOutput(BaseModel):
    """Output of the pydantic ai agent run."""

    is_task_failed: bool
    is_task_in_progress: bool
    is_input_required: bool
    output: str
    created_artifacts_paths: list[str]


def _task_failed_event(text: str, context_id: str | None, task_id: str | None) -> TaskStatusUpdateEvent:
    """Creates a TaskStatusUpdateEvent indicating task failure."""
    return TaskStatusUpdateEvent(
        status=TaskStatus(
            state=TaskState.failed, message=new_agent_text_message(text=text, context_id=context_id, task_id=task_id)
        ),
        final=True,
        context_id=context_id,
        task_id=task_id,
    )


def _task_cancelled_event(text: str, context_id: str | None, task_id: str | None) -> TaskStatusUpdateEvent:
    """Creates a TaskStatusUpdateEvent indicating task cancellation."""
    return TaskStatusUpdateEvent(
        status=TaskStatus(
            state=TaskState.canceled, message=new_agent_text_message(text=text, context_id=context_id, task_id=task_id)
        ),
        final=True,
        context_id=context_id,
        task_id=task_id,
    )


class PydanticAgentExecutor(AgentExecutor):
    """Agent Executor implementation using Pydantic AI agent - wrapper."""

    def __init__(self, agent_parameters: AgentParameters, history_storage: PydanticAiAgentHistoryStorage | None = None):
        self._agent_parameters = agent_parameters
        self._history_storage = history_storage if history_storage else InMemoryHistoryStorage()
        self._running_tasks: dict[str, asyncio.Task] = {}  # Track running agent tasks for cancellation

    def _convert_message_to_pydantic_parts(
        self,
        session_tuple: SessionIdTuple,
        message: Message,
    ) -> str | list[str | BinaryContent]:
        """Convert A2A Message to a Pydantic AI agent input format"""
        text_prompt = get_message_text(message)
        file_parts = get_file_parts(message.parts)
        if not file_parts:
            return text_prompt
        file_paths = [Path(part.uri) for part in file_parts if isinstance(part, FileWithUri)]

        return build_user_input(session_tuple, text_prompt, file_paths)

    async def execute(  # pylint: disable=too-many-locals
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Execute the agent run.
        Wraps pydantic ai agent execution with a2a protocol events
        Args:
            context (RequestContext): The request context containing the message and task information.
            event_queue (EventQueue): The event queue to enqueue events.
        """
        session_tuple = get_session_id_tuple()
        auth_token = auth_token_var.get()
        agent = self._build_agent(context, session_tuple, auth_token)
        if context.message is None:
            raise ValueError("No message provided")

        task = context.current_task
        message = context.message
        if not task:
            task = new_task(message)
            await event_queue.enqueue_event(task)

        if is_in_terminal_state(task):
            raise RuntimeError(f"Can not perform a task as it is in a terminal state: {task.status.state}")

        updater = TaskUpdater(event_queue, task.id, task.context_id)
        prompt = self._convert_message_to_pydantic_parts(session_tuple, message)
        history_message = await self._history_storage.get(task.id)

        # Create and track the agent run task for cancellation
        agent_task = asyncio.create_task(
            agent.run(
                user_prompt=prompt,
                message_history=history_message,
            )
        )
        self._running_tasks[task.id] = agent_task

        try:
            await updater.start_work()
            result = await agent_task
        except asyncio.CancelledError:
            # Task was cancelled, send cancellation event
            await updater.cancel()
            return
        except Exception as e:  # pylint: disable=broad-exception-caught
            await updater.failed(
                message=new_agent_text_message(
                    text=f"Agent execution error: {e}",
                    context_id=context.context_id,
                    task_id=task.id,
                ),
            )
            return
        finally:
            # Clean up the task from tracking
            self._running_tasks.pop(task.id, None)

        await self._history_storage.store(task.id, result.new_messages())

        run_output: RunOutput = result.output
        if run_output.is_task_failed:
            await updater.failed(
                message=new_agent_text_message(
                    text=f"Task failed: {run_output.output}",
                    context_id=context.context_id,
                    task_id=task.id,
                ),
            )
            return

        if run_output.is_input_required:
            await updater.requires_input(
                message=new_agent_text_message(text=run_output.output, context_id=context.context_id, task_id=task.id),
                final=False,
            )
            return

        if run_output.is_task_in_progress:
            logger.error("Task hasn't been completed: %s", run_output.output)
            await updater.failed(
                message=new_agent_text_message(
                    text=f"Agent didn't manage complete the task: {run_output.output}",
                    context_id=context.context_id,
                    task_id=task.id,
                ),
            )
            return

        for idx, artifact in enumerate(run_output.created_artifacts_paths):
            artifact_file = FileWithUri(uri=str(artifact), name=f"art_{idx}")
            await updater.add_artifact(
                parts=[Part(root=FilePart(file=artifact_file))],
                artifact_id=f"art_{idx}",
                last_chunk=True,
            )
        await updater.complete(
            message=new_agent_text_message(
                text=run_output.output,
                context_id=context.context_id,
                task_id=task.id,
            ),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the ongoing task identified by the task_id in the context.

        Attempts to stop the running agent task and publishes a TaskStatusUpdateEvent
        with state TaskState.canceled to the event_queue as per A2A SDK specification.

        Args:
            context: The request context containing the task ID to cancel.
            event_queue: The queue to publish the cancellation status update to.
        """
        task = context.current_task
        if not task:
            logger.warning("No task to cancel in context")
            return

        task_id = task.id

        # Check if we have a running task to cancel
        if task_id in self._running_tasks:
            agent_task = self._running_tasks[task_id]
            if not agent_task.done():
                logger.info("Cancelling running agent task: %s", task_id)
                agent_task.cancel()
                # The cancellation event will be sent by the execute method's except block
                return

        # If no running task found, check if task is already in terminal state
        if is_in_terminal_state(task):
            logger.info("Task %s is already in terminal state: %s", task_id, task.status.state)
            return

        # Send cancellation event for tasks that aren't currently running
        await event_queue.enqueue_event(
            _task_cancelled_event(
                text="Task cancelled",
                context_id=context.context_id,
                task_id=task_id,
            )
        )

    def _build_agent(
        self,
        _: RequestContext,
        session_tuple: SessionIdTuple,
        auth_token: str | None,
    ) -> Agent:
        params = self._agent_parameters
        mcp_servers = get_configured_mcp_servers(session_tuple, params.mcp_servers, auth_token=auth_token)
        return get_agent(
            system_prompt=params.system_prompt,
            toolsets=mcp_servers,
            output_type=RunOutput,
        )


def pydantic_agent_executor_factory(agent_parameters: AgentParameters) -> AgentExecutorFactory:
    """Factory function to create a PydanticAgentExecutor instance."""

    def create_agent_executor(engine: AsyncEngine | None) -> PydanticAgentExecutor:
        if engine is None:
            return PydanticAgentExecutor(agent_parameters)

        repo = PydanticAiMessageRepository(engine)
        history_storage = DatabasePydanticAiAgentHistoryStorage(repo)
        return PydanticAgentExecutor(agent_parameters, history_storage)

    return create_agent_executor
