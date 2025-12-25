"""Pydantic AI agent executor with test scenarios support."""

from pathlib import Path

from a2a.server.agent_execution import RequestContext
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncEngine

from aixtools.a2a.google_sdk.pydantic_ai_adapter.agent_executor import AgentParameters, PydanticAgentExecutor
from aixtools.a2a.google_sdk.pydantic_ai_adapter.db.repository import PydanticAiMessageRepository
from aixtools.a2a.google_sdk.pydantic_ai_adapter.db.storage import DatabasePydanticAiAgentHistoryStorage
from aixtools.a2a.google_sdk.pydantic_ai_adapter.storage import PydanticAiAgentHistoryStorage
from aixtools.a2a.google_sdk.types import AgentExecutorFactory
from aixtools.context import SessionIdTuple
from aixtools.testing.integration.a2a.utils import AixTestModelFactory, discover_test_models, get_test_mode_use_case


class PydanticAgentExecutorWithTestScenarios(PydanticAgentExecutor):
    """
    Pydantic AI agent executor extension that supports mocked agents for testing scenarios.
    """

    def __init__(
        self,
        agent_parameters: AgentParameters,
        history_storage: PydanticAiAgentHistoryStorage | None = None,
        mocked_model_factories: dict[str, AixTestModelFactory] = None,
    ):
        super().__init__(agent_parameters, history_storage)
        self._mocked_model_factories = mocked_model_factories if mocked_model_factories is not None else {}

    def _build_agent(
        self,
        context: RequestContext,
        session_tuple: SessionIdTuple,
        auth_token: str | None,
    ) -> Agent:
        agent = super()._build_agent(context, session_tuple, auth_token)
        test_mode_use_case = get_test_mode_use_case(context)
        if not test_mode_use_case:
            return agent

        model_factory = self._mocked_model_factories.get(test_mode_use_case)
        if model_factory is None:
            raise ValueError(f"Mocked model for test use case '{test_mode_use_case}' not found.")
        agent.model = model_factory(context, self._history_storage)
        return agent


def pydantic_agent_with_test_cases_executor_factory(
    agent_parameters: AgentParameters,
    *,
    path_to_mocked_models: Path,
    package_name: str,
) -> AgentExecutorFactory:
    """Factory function to create a PydanticAgentExecutor instance."""

    def create_agent_executor(engine: AsyncEngine | None) -> PydanticAgentExecutor:
        history_storage = None
        if engine is not None:
            repo = PydanticAiMessageRepository(engine)
            history_storage = DatabasePydanticAiAgentHistoryStorage(repo)

        mocked_model_factories = discover_test_models(path_to_mocked_models, package_name)
        return PydanticAgentExecutorWithTestScenarios(
            agent_parameters=agent_parameters,
            history_storage=history_storage,
            mocked_model_factories=mocked_model_factories,
        )

    return create_agent_executor
