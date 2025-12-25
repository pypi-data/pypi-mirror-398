"""Utilities for Agent-to-Agent (A2A) communication and task management."""

import asyncio
import uuid
from typing import Callable

from fasta2a import Skill
from fasta2a.client import A2AClient
from fasta2a.schema import GetTaskResponse, Message, Part, TextPart
from fastapi import status

from ..context import HTTP_SESSION_ID_HEADER, HTTP_USER_ID_HEADER
from ..server import get_session_id_tuple

SLEEP_TIME = 0.2
MAX_ITER = 1000
HTTP_OK = 200


def card2description(card):
    """Convert agent card to a description string."""
    descr = f"{card['name']}: {card['description']}\n"
    skills = card.get("skills", [])
    for skill in skills:
        descr += f"\t - {skill['name']}: {skill['description']}\n"
    return descr


async def fetch_agent_card(client: A2AClient) -> dict:
    """Request the Agent's card"""
    server_url = str(client.http_client.base_url).rstrip("/")
    agent_card_url = f"{server_url}/.well-known/agent.json"
    response = await client.http_client.get(agent_card_url, timeout=10)
    if response.status_code == status.HTTP_200_OK:
        card_data = response.json()
        return card_data
    raise Exception(f"Failed to retrieve agent card from {agent_card_url}. Status code: {response.status_code}")  # pylint: disable=broad-exception-raised


def get_result_text(ret: GetTaskResponse) -> str | None:
    """Extract the result text from the task result"""
    if "result" not in ret:
        return None
    result = ret["result"]
    if "artifacts" not in result:
        return None
    artifacts = result["artifacts"]
    for artifact in artifacts:
        if "parts" not in artifact:
            continue
        parts = artifact["parts"]
        for part in parts:
            if part["kind"] == "text":
                return part["text"]
    return None


async def poll_task(client: A2AClient, task_id: str) -> GetTaskResponse:
    """Polls the task status until it is completed or failed."""
    state = None
    for _ in range(MAX_ITER):
        ret = await client.get_task(task_id=task_id)
        # Check the state of the task
        state = ret["result"]["status"]["state"] if "result" in ret and "status" in ret["result"] else None
        if state == "completed":
            return ret
        if state == "failed":
            raise Exception("Task failed")  # pylint: disable=broad-exception-raised
        # Sleep for a while before checking again
        await asyncio.sleep(SLEEP_TIME)
    timeout_seconds = MAX_ITER * SLEEP_TIME
    raise Exception(f"Task did not complete in {timeout_seconds} seconds")  # pylint: disable=broad-exception-raised


async def submit_task(client: A2AClient, message: Message) -> str:
    """Send a message to the client and return task id."""
    user_id, session_id = get_session_id_tuple()
    msg = message.copy()
    msg["metadata"] = {
        **msg.get("metadata", {}),
        "user_id": client.http_client.headers.get(HTTP_USER_ID_HEADER, user_id),
        "session_id": client.http_client.headers.get(HTTP_SESSION_ID_HEADER, session_id),
    }
    ret = await client.send_message(message=msg)
    task_id = ret["result"]["id"] if "result" in ret and "id" in ret["result"] else ""
    return task_id


def multipart_message(parts: list[Part]) -> Message:
    """Create a message object"""
    message = Message(kind="message", role="user", parts=parts, message_id=str(uuid.uuid4()))
    return message


def text_message(text: str) -> Message:
    """Create a message object with a text part."""
    text_part = TextPart(kind="text", text=text, metadata={})
    return multipart_message([text_part])


async def task(client: A2AClient, text: str) -> GetTaskResponse:
    """Send a text message to the client and wait for task completion."""
    msg = text_message(text)
    task_id = await submit_task(client, msg)
    print(f"Task ID: {task_id}")
    ret = await poll_task(client, task_id)
    return ret


def tool2skill(tool: Callable) -> Skill:
    """Convert a tool to a skill."""
    return Skill(
        id=tool.__name__,
        name=tool.__name__,
        description=tool.__doc__ or "",
    )  # type: ignore
