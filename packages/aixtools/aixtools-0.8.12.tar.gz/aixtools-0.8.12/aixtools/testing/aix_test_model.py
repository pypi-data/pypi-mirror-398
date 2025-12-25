"""
Test model implementation for AI agent testing with predefined responses.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import AsyncGeneratorType

from pydantic import BaseModel
from pydantic_ai.messages import FinishReason, ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models import Model, ModelRequestParameters, StreamedResponse
from pydantic_ai.models.function import _estimate_usage
from pydantic_ai.models.test import TestStreamedResponse
from pydantic_ai.settings import ModelSettings

from ..utils.utils import async_iter

FINAL_RESULT_TOOL_NAME = "final_result"

# Type aliases for cleaner type hints
ResponseItem = str | TextPart | ToolCallPart


def _convert_to_parts(items: list[ResponseItem]) -> list[TextPart | ToolCallPart]:
    """Convert a list of strings, TextParts, or ToolCallParts to a list of Parts."""
    parts: list[TextPart | ToolCallPart] = []
    for item in items:
        match item:
            case str():
                parts.append(TextPart(item))
            case TextPart() | ToolCallPart():
                parts.append(item)
            case _:
                raise ValueError(f"Invalid item type in list: {type(item)}, item: {item}")
    return parts


def final_result_tool(result: BaseModel | dict) -> ToolCallPart:
    """Create a ToolCallPart for the final result."""
    if isinstance(result, BaseModel):
        args = result.model_dump()
    else:
        args = result
    return ToolCallPart(tool_name=FINAL_RESULT_TOOL_NAME, args=args)


class AixTestFinishReason:  # pylint: disable=too-few-public-methods
    """Wraps a response item for AixTestModel to emulate a custom finish reason from the model."""

    def __init__(
        self,
        reason: FinishReason,
        response: ResponseItem | list[ResponseItem] | None = None,
    ):
        self.reason: FinishReason = reason
        match response:
            case list():
                self.parts = _convert_to_parts(response)
            case str() | TextPart() | ToolCallPart():
                self.parts = _convert_to_parts([response])
            case _:
                self.parts = []


class AixTestModel(Model):
    """
    Test model, returns a specified list of answers, including messages or tool calls
    This is used for testing the agent and model interaction with the rest of the system.

    responses: Is a list of response items that the model will return in order. Each item can be:
        - str: A simple text response
        - TextPart: A text part
        - ToolCallPart: A tool call
        - list[str | TextPart | ToolCallPart]: Multiple parts in a single response
        - AixTestFinishReason: Emulate a custom finish reason from the model with optional response parts

    Note: The agent will continue to invoke 'request()' until it returns a txt (i.e. not a ToolCallPart).

    Example: Unstructured output (text)
    ```
        model = AixTestModel(
                    responses=[
                        ToolCallPart(tool_name='send_message_to_user', args={'message': 'First, let me say hi...'}),
                        "Please invoke the agent again to continue the conversation....",
                        # ---------- The first time you invoke the agent, it will stop here ----------

                        ToolCallPart(tool_name='send_message_to_user', args={'message': 'Hi there again!'}),
                        "The 10th prime number is 29.",
                        # ---------- The second time you invoke the agent, it will stop here ----------

                        # If you invoke the agent again, it will continue raising an exception
                        # because there are no more responses
                    ]
                )
    ```

    Example structured output:
    ```
        # Define a model for the final result
        class MyResult(BaseModel):
            text: str

        model = AixTestModel(
                    responses=[
                        ToolCallPart(tool_name='send_message_to_user', args={'message': 'First, let me say hi...'}),
                        ToolCallPart(tool_name='send_message_to_user', args={'message': 'Hi there again!'}),
                        final_result_tool(MyResult(text='The 10th prime is 29')),
                    ]
                )
    ```

    Example with multiple parts in a single response:
    ```
        model = AixTestModel(
                    responses=[
                        [
                            "First, let me think about this...",
                            ToolCallPart(tool_name='analyze', args={'data': 'xyz'}),
                            TextPart("Analysis complete."),
                        ],
                        "Final answer after analysis.",
                    ]
                )
    ```

    Example with custom finish reason:
    ```
        model = AixTestModel(
                    responses=[
                        ToolCallPart(tool_name='send_message_to_user', args={'message': 'Processing...'}),
                        AixTestFinishReason(
                            reason='content_filter',
                        ),
                    ]
                )
    ```
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        responses: list[ResponseItem | list[ResponseItem] | AixTestFinishReason] | AsyncGeneratorType,
        sleep_time: float | None = None,
    ):
        self.response_iter = responses(self) if callable(responses) else async_iter(responses)
        self.messages: list[ModelMessage] = None
        self.sleep_time = sleep_time
        self.last_model_request_parameters: ModelRequestParameters | None = None

    @property
    def last_message(self) -> ModelResponse | None:
        """Return the last response."""
        return self.messages[-1] if self.messages else None

    @property
    def last_message_part(self) -> TextPart | ToolCallPart | None:
        """Return the last part of the response."""
        return self.last_message.parts[-1] if self.last_message and self.last_message.parts else None

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        self.last_model_request_parameters = model_request_parameters
        model_response = await self._request(messages, model_settings, model_request_parameters)
        model_response.usage = _estimate_usage([*messages, model_response])
        return model_response

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        *args,  # pylint: disable=unused-argument # Accept additional arguments for compatibility with pydantic-ai 1.0.9
        **kwargs,  # pylint: disable=unused-argument
    ) -> AsyncIterator[StreamedResponse]:
        model_response = await self._request(messages, model_settings, model_request_parameters)
        response = TestStreamedResponse(
            _model_name=self.model_name,
            _structured_response=model_response,
            _messages=messages,
            model_request_parameters=model_request_parameters,
            _provider_name="",
        )
        response.finish_reason = model_response.finish_reason
        yield response

    @property
    def model_name(self) -> str:
        return self.__class__.__name__.lower()

    @property
    def system(self) -> str:
        """The system / model provider."""
        return "test_system"

    async def _request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,  # pylint: disable=unused-argument
        model_request_parameters: ModelRequestParameters,  # pylint: disable=unused-argument
    ) -> ModelResponse:
        self.messages = messages
        res = await anext(self.response_iter, None)
        assert res, "No more responses available."
        if callable(res):
            res = res(self, messages)

        finish_reason: FinishReason | None = None

        match res:
            case Exception():
                raise res
            case list():
                parts = _convert_to_parts(res)
            case str() | TextPart() | ToolCallPart():
                parts = _convert_to_parts([res])
            case AixTestFinishReason():
                parts = res.parts
                finish_reason = res.reason
            case _:
                raise ValueError(f"Invalid response type: {type(res)}, response: {res}")
        if self.sleep_time:
            await asyncio.sleep(self.sleep_time)
        return ModelResponse(parts=parts, model_name=self.model_name, finish_reason=finish_reason)
