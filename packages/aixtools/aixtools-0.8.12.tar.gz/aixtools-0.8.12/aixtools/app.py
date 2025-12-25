#!/usr/bin/env python3

"""
Simple Chainlit app example
"""

import traceback

import chainlit as cl
from pydantic_graph import End

from aixtools.agents.agent import get_agent
from aixtools.logging.logging_config import get_logger
from aixtools.utils.chainlit import cl_agent_show

logger = get_logger(__name__)

HISTORY = "history"

SYSTEM_PROMPT = """
You are a helpful assistant.
"""


@cl.step
async def greet_tool(msg: str) -> str:
    """A simple greeting tool"""
    return f"Hello! You said: {msg}"


async def parse_user_message(message):
    """Parse user message and check if it is a command"""
    # When we type something that starts with ':', we are using a "command" (i.e. it does not go to the agent)
    command = str(message.content).strip().lower()
    if command.startswith(":"):
        logger.debug("Received command: %s", command)
        match command:
            case ":clear":
                # Clear the history
                cl.user_session.set(HISTORY, [])
                return None
            case ":help":
                # Show help
                help_message = """
                Available commands:
                - :clear: Clear the chat history
                - :help: Show this help message
                """
                await cl.Message(content=help_message).send()
                return None
            case ":history":
                # Show history
                history = cl.user_session.get(HISTORY)
                if history:
                    history_message = "\n".join(history)
                    await cl.Message(content=f"Chat history:\n{history_message}").send()
                else:
                    await cl.Message(content="No history available.").send()
                return None
            case _:
                # Unknown command
                await cl.Message(content=f"Unknown command: {command}").send()
                return None
    else:
        user_message = message.content
        logger.debug("User message: %s", user_message)
    return user_message


async def run_agent(messages):
    """Run the agent with the given messages"""
    agent = get_agent(system_prompt=SYSTEM_PROMPT, tools=[greet_tool])
    ret = ""
    msg = cl.Message(content="")
    await msg.send()
    try:
        ret = await cl_agent_show.show_run(agent=agent, prompt=messages, msg=msg, debug=False)
    except Exception as e:  # pylint: disable=broad-exception-caught
        msg.elements.append(cl.Text(name="Error", content=f"Error: {e}", type="error"))  # pylint: disable=unexpected-keyword-arg
        logger.error("Error: %s", e)
        # Log the full stack trace for debugging
        stack_trace = traceback.format_exc()
        logger.error("Stack tarace:\n%s", stack_trace)
        logger.error("Stack trace:\n%s", stack_trace)
        msg.elements.append(cl.Text(name="Stack Trace", content=stack_trace, language="python"))
        ret = f"Internal server error: {e}"
    await msg.send()
    return ret


def update_history(history, user_message=None, run_return=None):
    """Update history with user message and model run output"""
    assert user_message is not None or run_return is not None, "Either user message or run return must be provided"
    if user_message is not None:
        logger.debug("Updating history: Got user message type %s: %s", type(user_message), user_message)
        assert isinstance(user_message, str)
        history.append(user_message)
    if run_return is not None:
        logger.debug("Updating history: Got agent output type %s: %s", type(run_return), run_return)
        latest_item = ""
        if isinstance(run_return, list):
            # If it is a list of 'node' items, the last element is the 'end_message' with the final result
            end_message: End = run_return[-1]
            final_result = end_message.data
            latest_item = str(final_result.data)
        else:
            latest_item = str(run_return)
        # Update history and store it
        logger.debug("Updating history: Adding to history type %s: %s", type(latest_item), latest_item)
        history.append(latest_item)
    return history


@cl.set_starters
async def set_starters():
    """Set the starters"""
    return [
        cl.Starter(label="Message", message="Hello world!"),
    ]


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session by resetting history when a new chat starts."""
    # Reset history
    logger.debug("On chat start")
    cl.user_session.set(HISTORY, [])


@cl.on_message
async def on_message(message: cl.Message):
    """Process incoming chat messages and generate responses using the agent."""
    history = cl.user_session.get(HISTORY)  # Get user message and history
    user_message = await parse_user_message(message)  # Parse user message
    # Check if user message is None (e.g. if it is a command)
    if user_message is None:
        return
    messages = update_history(history, user_message=user_message)  # Update history with user message
    # Run the agent
    run_return = await run_agent(messages)
    # Update history and store it
    history = update_history(history, run_return=run_return)
    cl.user_session.set(HISTORY, messages)
