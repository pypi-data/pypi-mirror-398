"""
This module provides functionality to convert a Pydantic AI Agent into a FastA2A application
"""

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial
from typing import assert_never

import httpx
from a2a.server.agent_execution import AgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    DatabasePushNotificationConfigStore,
    DatabaseTaskStore,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
    PushNotificationConfigStore,
    TaskStore,
)
from a2a.types import AgentCard
from fasta2a.applications import FastA2A
from fasta2a.broker import InMemoryBroker
from fasta2a.schema import Part, TaskSendParams
from fasta2a.storage import InMemoryStorage
from pydantic_ai import Agent
from pydantic_ai._a2a import AgentWorker, worker_lifespan
from pydantic_ai.messages import (
    AudioUrl,
    BinaryContent,
    DocumentUrl,
    ImageUrl,
    ModelRequestPart,
    UserPromptPart,
    VideoUrl,
)
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

from aixtools.a2a.auth_middleware import AuthMiddleware
from aixtools.a2a.auth_push_notification_sender import AuthenticatedPushNotificationSender
from aixtools.a2a.context_middleware import A2AContextMiddleware
from aixtools.a2a.google_sdk.types import AgentExecutorFactory
from aixtools.auth.auth import AccessTokenAuthProvider
from aixtools.context import session_id_var, user_id_var
from aixtools.utils import config

logger = logging.getLogger(__name__)


class AgentWorkerWithMetadataParser(AgentWorker):
    """Custom AgentWorker class that extracts the session metadata from message metadata."""

    async def run_task(self, params: TaskSendParams) -> None:
        """
        Extract session metadata from message and store them in context variables,
        then call the parent class's run_task method.
        """
        # Load the task to extract metadata
        task = await self.storage.load_task(params["id"])
        if task:
            # Extract headers from message metadata if available
            if message := (task.get("history") or [None])[-1]:
                metadata = message.get("metadata", {})
                # Store in context variables
                user_id_var.set(metadata.get("user_id", ""))
                session_id_var.set(metadata.get("session_id", ""))
        # Call the parent class's run_task method
        return await super().run_task(params)


class AgentWorkerWithDataPartSupport(AgentWorkerWithMetadataParser):
    """Custom agent worker that adds support for data parts in messages."""

    def _request_parts_from_a2a(self, parts: list[Part]) -> list[ModelRequestPart]:
        """
        Clones underlying method with additional support for data parts.
        TODO: remove once pydantic-ai supports data parts natively.
        """
        model_parts: list[ModelRequestPart] = []
        for part in parts:
            if part["kind"] == "text":
                model_parts.append(UserPromptPart(content=part["text"]))
            elif part["kind"] == "file":
                file_content = part["file"]
                if "bytes" in file_content:
                    data = file_content["bytes"].encode("utf-8")
                    mime_type = file_content.get("mime_type", "application/octet-stream")
                    content = BinaryContent(data=data, media_type=mime_type)
                    model_parts.append(UserPromptPart(content=[content]))
                else:
                    url = file_content["uri"]
                    for url_cls in (DocumentUrl, AudioUrl, ImageUrl, VideoUrl):
                        content = url_cls(url=url)
                        try:
                            content.media_type
                        except ValueError:  # pragma: no cover
                            continue
                        else:
                            break
                    else:
                        raise ValueError(f"Unsupported file type: {url}")  # pragma: no cover
                    model_parts.append(UserPromptPart(content=[content]))
            elif part["kind"] == "data":
                content = json.dumps(part["data"])
                model_parts.append(UserPromptPart(content=[content]))
            else:
                assert_never(part)
        return model_parts


def agent_to_a2a(  # pylint: disable=too-many-arguments
    agent: Agent,
    name: str,
    description: str,
    skills: list[dict],
    worker_class=AgentWorkerWithMetadataParser,
    *,
    auth_provider: AccessTokenAuthProvider | None = None,
) -> FastA2A:
    """Convert the agent to an A2A application taking care of session metadata extraction."""
    storage = InMemoryStorage()
    broker = InMemoryBroker()
    worker = worker_class(broker=broker, storage=storage, agent=agent)
    app = FastA2A(
        storage=storage,
        broker=broker,
        name=name,
        description=description,
        skills=skills,
        url="",
        lifespan=partial(worker_lifespan, worker=worker, agent=agent),
    )
    auth_provider = None if config.SKIP_MCP_AUTHORIZATION else auth_provider or AccessTokenAuthProvider()
    app.add_middleware(AuthMiddleware, provider=auth_provider)
    return app


def fix_a2a_docs_pages(app: Starlette) -> None:
    """
    Fix the FastA2A documentation to point to the correct path.
    This is a workaround for the issue with the FastA2A docs not being served correctly
    when mounted as a sub-path.
    """

    async def redirect_to_sub_agent(request: Request):
        """Redirect to proper sub-app using the Referer header to determine the path prefix."""
        referer = request.headers.get("referer", "")
        if referer.endswith("/docs"):
            return RedirectResponse(url=f"{referer.rsplit('/', 1)[0]}{request.url.path}")
        raise HTTPException(status_code=404)

    app.router.add_route("/.well-known/agent.json", redirect_to_sub_agent, methods=["GET"])
    app.router.add_route("/", redirect_to_sub_agent, methods=["POST"])


def create_handler_with_lifespan(
    agent_executor: AgentExecutor,
    task_store: TaskStore,
    push_config_store: PushNotificationConfigStore,
    push_timeout_seconds: int,
):
    """
    Returns both handler and lifespan that will initialize it.

    Args:
        agent_executor: Executor for running agent tasks
        task_store: Store for managing tasks
        push_config_store: Store for push notification configurations
        push_timeout_seconds: Timeout for push notification requests
    """
    handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
        push_config_store=push_config_store,
        push_sender=None,
    )

    @asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[dict]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(push_timeout_seconds)) as client:
            handler._push_sender = AuthenticatedPushNotificationSender(  # pylint: disable=protected-access
                httpx_client=client,
                config_store=push_config_store,
            )
            handler._push_config_store = push_config_store  # pylint: disable=protected-access
            yield {}

    return handler, lifespan


def create_task_store(engine: AsyncEngine | None = None) -> TaskStore:
    """
    Creating TaskStore instance.

    Args:
        engine: SQLAlchemy async engine for database task store. If None, returns InMemoryTaskStore.

    Returns:
        TaskStore instance (either DatabaseTaskStore or InMemoryTaskStore)
    """
    if engine is None:
        return InMemoryTaskStore()

    task_store = DatabaseTaskStore(engine=engine, create_table=False)
    logger.info("A2A database task store initialized successfully")
    return task_store


def create_push_notification_config_store(engine: AsyncEngine | None = None) -> PushNotificationConfigStore:
    """
    Creating PushNotificationConfigStore instance.

    Args:
        engine: SQLAlchemy async engine for database push config store.
        If None, returns InMemoryPushNotificationConfigStore.

    Returns:
        PushNotificationConfigStore instance (either database-backed or in-memory)
    """
    if engine is None:
        return InMemoryPushNotificationConfigStore()

    return DatabasePushNotificationConfigStore(engine=engine, create_table=False)


def build_a2a_starlette_app(  # noqa: PLR0913 pylint: disable=too-many-arguments,too-many-positional-arguments
    public_agent_card: AgentCard,
    agent_executor: AgentExecutor | AgentExecutorFactory,
    auth_provider: AccessTokenAuthProvider | None = None,
    database_url: str | None = None,
    enable_push_notifications: bool = False,
    push_timeout_seconds: int = 60,
) -> Starlette:
    """
    Build A2A Starlette app with auth middleware.

    This function creates a Starlette application with a lifespan context manager that
    manages the httpx.AsyncClient lifecycle when push notifications are enabled.

    Args:
        public_agent_card: Agent card describing the agent
        agent_executor: Agent executor (used to create handler if request_handler not provided)
        auth_provider: Auth provider (defaults to AccessTokenAuthProvider)
        database_url: Database URL for creating database stores.
        enable_push_notifications: Enable push notifications when creating handler
        push_timeout_seconds: Timeout for push notification HTTP requests

    Returns:
        Configured Starlette application
    """
    if agent_executor is None:
        raise ValueError("agent_executor must be provided")

    engine = None
    if database_url:
        engine = create_async_engine(
            database_url,
            pool_size=10,
            pool_pre_ping=True,
        )

    lifespan = None
    task_store = create_task_store(engine)
    push_config_store = create_push_notification_config_store(engine)

    executor = agent_executor if isinstance(agent_executor, AgentExecutor) else agent_executor(engine)

    if enable_push_notifications:
        handler, lifespan = create_handler_with_lifespan(
            agent_executor=executor,
            task_store=task_store,
            push_config_store=push_config_store,
            push_timeout_seconds=push_timeout_seconds,
        )
    else:
        handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=task_store,
        )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=handler,
    )

    if config.SKIP_MCP_AUTHORIZATION:
        auth_provider = None
    elif auth_provider is None:
        auth_provider = AccessTokenAuthProvider()

    app = server.build(lifespan=lifespan)

    app.add_middleware(A2AContextMiddleware)
    if auth_provider:
        app.add_middleware(AuthMiddleware, provider=auth_provider)
    return app
