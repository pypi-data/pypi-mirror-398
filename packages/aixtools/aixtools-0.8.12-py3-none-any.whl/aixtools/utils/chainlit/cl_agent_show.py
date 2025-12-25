import chainlit as cl
import rich
from pydantic_ai import Agent
from pydantic_ai.messages import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ToolCallPartDelta,
)

from aixtools.logging.log_objects import ObjectLogger


def _show_debug_info(debug, *args):
    if debug:
        rich.print(*args)


async def show_run(agent: Agent, prompt, msg: cl.Message, debug=False, verbose=True):  # noqa: PLR0912
    """Run an agent with a prompt and send the results to a message."""
    nodes = []
    async with agent.iter(prompt) as run:
        with ObjectLogger(debug=debug, verbose=verbose) as agent_logger:
            async for node in run:
                nodes.append(node)
                agent_logger.log(node)
                if Agent.is_user_prompt_node(node):
                    # A user prompt node => The user has provided input
                    _show_debug_info(debug, "=== UserPromptNode: ", node)
                elif Agent.is_model_request_node(node):
                    # A model request node => We can stream tokens from the model's request
                    _show_debug_info(debug, "=== ModelRequestNode: streaming partial request tokens ===")
                    async with node.stream(run.ctx) as request_stream:
                        async for event in request_stream:
                            if isinstance(event, PartStartEvent):
                                _show_debug_info(debug, f"[Request] Starting part {event.index}: ", event.part)
                            elif isinstance(event, PartDeltaEvent):
                                if isinstance(event.delta, TextPartDelta):
                                    _show_debug_info(
                                        debug,
                                        (
                                            "[ModelRequestNone / PartDeltaEvent / TextPartDelta] "
                                            f"Part {event.index}: {event.delta.content_delta}"
                                        ),
                                    )
                                    await msg.stream_token(event.delta.content_delta)
                                elif isinstance(event.delta, ToolCallPartDelta):
                                    _show_debug_info(
                                        debug,
                                        f"[ModelRequestNone / PartDeltaEvent / ToolCallPartDelta] Part {event.index}, ",
                                        event.delta,
                                    )
                            elif isinstance(event, FinalResultEvent):
                                _show_debug_info(
                                    debug, f"[Result] The model produced a final result (tool_name={event.tool_name})"
                                )
                elif Agent.is_call_tools_node(node):
                    # A handle-response node => The model returned some data, potentially calls a tool
                    _show_debug_info(debug, "=== CallToolsNode: streaming partial response & tool usage ===")
                    async with node.stream(run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                _show_debug_info(
                                    debug,
                                    (
                                        f"[Tools] The LLM calls tool={event.part.tool_name!r} "
                                        f"with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})"
                                    ),
                                )
                            elif isinstance(event, FunctionToolResultEvent):
                                _show_debug_info(
                                    debug,
                                    f"[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}",
                                )
                elif Agent.is_end_node(node):
                    assert run.result.output == node.data.output
                    # Once an End node is reached, the agent run is complete
                    _show_debug_info(debug, f"=== Final Agent Output: {run.result.output} ===")
    return run.result.output
