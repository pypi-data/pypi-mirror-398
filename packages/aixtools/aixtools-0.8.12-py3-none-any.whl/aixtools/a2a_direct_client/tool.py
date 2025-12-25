"""Tools for building PydanticAI toolsets from A2A agents."""

import re
from functools import partial
from typing import Any, Tuple
from uuid import uuid4

import httpx
from a2a.types import AgentCard, Artifact, Message, Part, Role, Task, TaskState, TextPart
from pydantic import BaseModel
from pydantic_ai.tools import Tool
from pydantic_ai.toolsets import FunctionToolset

from aixtools.a2a.google_sdk.remote_agent_connection import RemoteAgentConnection
from aixtools.a2a.google_sdk.utils import get_agent_card
from aixtools.a2a_direct_client.client import A2AClientWithBearerAuth


class AgentResponse(BaseModel):
    """Result of invoking a remote agent."""

    task_id: str
    state: TaskState
    text_message: str | None
    artifacts: list[Artifact] | None = []


# Helper functions
def _get_text_from_message(msg: Message) -> str:
    texts = [part.root.text for part in msg.parts if isinstance(part.root, TextPart)]
    return "".join(texts)


def _get_text_from_task(task: Task) -> str:
    msg = task.status.message
    return _get_text_from_message(msg) if msg else ""


def _build_agent_tool_description(card: AgentCard) -> str:
    """
    Build tool description for the agent as a whole.
    The agent will internally route the prompt to the most appropriate skill.
    """
    lines: list[str] = [f"Agent: {card.name}."]

    if card.description:
        lines.append(card.description)

    if card.skills:
        lines.append("Agent skills:")
        for skill in card.skills:
            line = f"- {skill.name} (id='{skill.id}')"
            if skill.description:
                line += f": {skill.description}"
            lines.append(line)

    return "\n".join(lines)


def _agent_tool_schema(card: AgentCard) -> dict[str, Any]:
    """
    Schema for the agent tool when the agent auto-routes the prompt.
    Only exposes a single `prompt` field.
    """
    examples: list[str] = []
    for skill in card.skills or []:
        examples.extend(skill.examples or [])

    card_description = _build_agent_tool_description(card)
    examples_text = "\n".join(f"- {ex}" for ex in examples[:3])  # limit to a few

    return {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": f"{card_description}Example requests:\n{examples_text}".strip(),
            },
        },
        "required": ["prompt"],
    }


async def _call_agent(  # pylint: disable=too-many-arguments
    prompt: str, conn: RemoteAgentConnection
) -> AgentResponse:
    """
    Send a prompt to a remote A2A agent via RemoteAgentConnection and return text.
    """

    message = Message(
        role=Role.user,
        parts=[Part(root=TextPart(text=prompt))],
        message_id=uuid4().hex,
    )

    result = await conn.send_message_with_polling(message)

    if isinstance(result, Task):
        task_status = result.status
        text_message = None
        if task_status.message:
            text_message = _get_text_from_task(result)
        return AgentResponse(
            task_id=result.id,
            state=task_status.state,
            artifacts=result.artifacts,
            text_message=text_message,
        )

    if isinstance(result, Message):
        return AgentResponse(
            task_id=result.id,
            state=TaskState.completed,
            artifacts=[],
            text_message=_get_text_from_message(result),
        )

    raise ValueError(f"Unexpected result type: {type(result)}")


async def _get_agent_connection_and_card(
    agent_url: str,
    timeout: int,
    session_id: str,
) -> Tuple[AgentCard, RemoteAgentConnection]:
    """
    Create a RemoteAgentConnection for the given agent URL and AgentCard.
    """
    httpx_client = httpx.AsyncClient(
        base_url=agent_url,
        timeout=timeout,
        headers={"session-id": session_id},
    )
    card = await get_agent_card(httpx_client, agent_url)
    client = await A2AClientWithBearerAuth.create(card, httpx_client=httpx_client)
    remote_connection = RemoteAgentConnection(card, client)
    return card, remote_connection


def _agent_tool_name(card: AgentCard) -> str:
    """
    Derive a tool name from the agent card name
    """
    base = card.name
    base = base.strip().lower().replace(" ", "_")
    base = re.sub(r"[^0-9a-zA-Z_]", "_", base)
    return base


def _build_toolset_for_card(
    card: AgentCard,
    remote_connection: RemoteAgentConnection,
) -> FunctionToolset[None]:
    """
    Build a PydanticAI toolset from an AgentCard and a RemoteAgentConnection.

    Exposes a single tool per agent:
      - argument: prompt (string)
      - behavior: send prompt to agent, agent chooses internal skill.
    """
    toolset: FunctionToolset[None] = FunctionToolset()

    description = _build_agent_tool_description(card)
    agent_schema = _agent_tool_schema(card)
    tool_name = _agent_tool_name(card)

    agent_tool = Tool.from_schema(
        function=partial(_call_agent, conn=remote_connection),
        name=tool_name,
        description=description,
        json_schema=agent_schema,
    )

    toolset.add_tool(agent_tool)
    return toolset


class AgentToolset:  # pylint: disable=too-few-public-methods
    """Pydantic-AI model toolset builder."""

    @staticmethod
    async def create(agent_url: str, *, timeout: int = 60, session_id: str | None = None) -> FunctionToolset[None]:
        """
        Create a PydanticAI toolset from an AgentCard retrieved from the given Agent URL.

        The resulting toolset will contain a single tool for this agent which accepts only `prompt`.
        """
        if session_id is None:
            session_id = str(uuid4())

        card, remote_connection = await _get_agent_connection_and_card(
            agent_url=agent_url,
            timeout=timeout,
            session_id=session_id,
        )

        return _build_toolset_for_card(card, remote_connection)
