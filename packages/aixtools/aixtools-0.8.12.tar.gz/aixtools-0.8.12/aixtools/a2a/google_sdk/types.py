"""Types for Google SDK integration in A2A."""

from typing import Callable, Optional

from a2a.server.agent_execution import AgentExecutor
from sqlalchemy.ext.asyncio import AsyncEngine

AgentExecutorFactory = Callable[[Optional[AsyncEngine]], AgentExecutor]
