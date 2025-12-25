#!/usr/bin/env python3
"""
Faulty MCP Server for Testing MCP Errors
- Simulates 404 errors for specific MCP requests
"""

import argparse
import asyncio
import json
import logging.config
import os
from dataclasses import dataclass
from random import choice, random

from fastapi import HTTPException, status
from fastmcp import FastMCP
from fastmcp.exceptions import (
    ClientError,
    DisabledError,
    InvalidSignature,
    NotFoundError,
    PromptError,
    ResourceError,
    ToolError,
    ValidationError,
)
from fastmcp.server.middleware import Middleware as McpMiddleware
from fastmcp.server.middleware import MiddlewareContext
from fastmcp.server.middleware.logging import LoggingMiddleware
from starlette.middleware import Middleware as StarletteMiddleware
from starlette.types import Receive, Scope, Send

from aixtools.logging.logging_config import DEFAULT_LOGGING_CONFIG
from aixtools.utils import get_logger

# Remove the user/session ID from logger line to shorten it
DEFAULT_LOGGING_CONFIG["formatters"]["color"]["format"] = (
    "%(log_color)s%(asctime)s.%(msecs)03d %(levelname)-8s%(reset)s %(message)s"
)
logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)

# Get the logger
logger = get_logger(__name__)


@dataclass
class Config:
    """Global configuration for the faulty MCP server."""

    port: int = 9999
    prob_on_post_404: float = 0.5  # Probability of injecting a 404 error for POST requests
    prob_on_get_crash: float = 0.3  # Probability of terminating the process on GET request
    prob_on_delete_404: float = 0.5  # Probability of injecting a 404 error for DELETE requests
    prob_in_list_tools_throw: float = 0.5  # Probability of throwing an exception in list tools handling
    prob_in_list_tools_crash: float = 0.3  # Probability of terminating the process in list tools handling


# Global configuration
config = Config()


class McpErrorMiddleware(McpMiddleware):
    """Custom middleware to simulate errors in MCP requests."""

    async def __call__(self, context: MiddlewareContext, call_next):
        # This method receives ALL messages regardless of type
        logger.info("[McpErrorMiddleware] processing: %s", context.method)

        if context.method == "tools/list":
            random_number = random()
            logger.info("[McpErrorMiddleware] random number: %f", random_number)
            if random_number < config.prob_in_list_tools_crash:
                logger.warning("[McpErrorMiddleware] Simulating server crash!")
                os.kill(os.getpid(), 9)

            if random_number < config.prob_in_list_tools_throw:
                exception_class = choice(
                    [
                        ValidationError,
                        ResourceError,
                        ToolError,
                        PromptError,
                        InvalidSignature,
                        ClientError,
                        NotFoundError,
                        DisabledError,
                    ]
                )
                logger.warning("[McpErrorMiddleware] throwing %s for: %s", exception_class.__name__, context.method)
                raise exception_class(f"[McpErrorMiddleware] {exception_class.__name__}.")

        result = await call_next(context)
        logger.info("[McpErrorMiddleware] completed: %s", context.method)
        return result


class StarletteErrorMiddleware:  # pylint: disable=too-few-public-methods
    """Custom Starlette middleware to log and inject errors."""

    def __init__(self, app):
        """Initialize middleware."""
        self.app = app
        logger.info("[StarletteErrorMiddleware] Middleware initialized!")
        logger.info("Current configuration:")
        logger.info("HTTP 404 on POST request probability: %f", config.prob_on_post_404)
        logger.info("Terminate on GET request probability: %f", config.prob_on_get_crash)
        logger.info("HTTP 404 on DELETE request probability: %f", config.prob_on_delete_404)
        logger.info("Exception in list tools handling probability: %f", config.prob_in_list_tools_throw)
        logger.info("Terminate in list handle probability: %f", config.prob_in_list_tools_crash)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):  # noqa: PLR0915 # pylint: disable=too-many-statements
        # Log all the condition variables for debugging

        logger.info("[StarletteErrorMiddleware] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        logger.info("[StarletteErrorMiddleware] scope['type']: %s", scope.get("type", "unknown"))
        logger.info("[StarletteErrorMiddleware] scope['path']: %s", scope.get("path", "unknown"))
        logger.info("[StarletteErrorMiddleware] HTTP method: %s", http_method := scope.get("method", "unknown"))
        logger.info("[StarletteErrorMiddleware] Headers: %s", str(dict(scope.get("headers", []))))

        # Wrap receive to log body content without breaking the flow
        body_parts = []
        should_inject_404 = False

        if http_method == "DELETE":
            random_number = random()
            logger.info("[StarletteErrorMiddleware] random number: %f", random_number)
            if random_number < config.prob_on_delete_404:
                logger.info("[StarletteErrorMiddleware] Simulating 404 error on DELETE request")
                should_inject_404 = True

        async def logging_receive():
            nonlocal should_inject_404
            message = await receive()
            logger.info("[StarletteErrorMiddleware] Received message: %s", str(message))

            if message["type"] == "http.request":  # pylint: disable=too-many-nested-blocks
                if http_method == "GET":
                    random_number = random()
                    logger.info("[StarletteErrorMiddleware] random number: %f", random_number)
                    if random_number < config.prob_on_get_crash:
                        logger.warning("[StarletteErrorMiddleware] Simulating server crash on GET request!")
                        os.kill(os.getpid(), 9)

                body = message.get("body", b"")
                if body:
                    body_parts.append(body)

                # Log when we have the complete body
                if not message.get("more_body", False):
                    complete_body = b"".join(body_parts)
                    if complete_body:
                        try:
                            body_str = complete_body.decode("utf-8")
                            logger.info("[StarletteErrorMiddleware] Request body: %s", body_str)

                            json_data = json.loads(body_str)
                            if isinstance(json_data, dict):
                                method_name = json_data.get("method", "unknown")
                                if method_name == "initialize" and not json_data.get("params", {}).get("capabilities"):
                                    logger.info("Detected initial health check from Navari, skipping 404 injection.")
                                    return message
                                logger.info("[StarletteErrorMiddleware] MCP method: %s", method_name)

                                # Check if we should inject 404
                                random_number = random()
                                logger.info("[StarletteErrorMiddleware] random number: %f", random_number)
                                if random_number < config.prob_on_post_404:
                                    should_inject_404 = True
                                    logger.info("[StarletteErrorMiddleware] %s - will inject 404!", method_name)
                        except (UnicodeDecodeError, json.JSONDecodeError) as e:
                            logger.exception("[StarletteErrorMiddleware] Error parsing body: %s", e)
                    else:
                        logger.info("[StarletteErrorMiddleware] Request body: (empty)")

            return message

        async def intercepting_send(message):
            logger.info("[StarletteErrorMiddleware] Sending message: %s", str(message))
            if message["type"] == "http.response.start" and should_inject_404:
                logger.warning("[StarletteErrorMiddleware] Injecting 404!")
                # Replace the response with 404
                message = {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [[b"content-type", b"text/plain"]],
                }
            elif message["type"] == "http.response.body" and should_inject_404:
                # Replace body with 404 message
                message = {
                    "type": "http.response.body",
                    "body": b"Simulated 404 error",
                }

            await send(message)

        logger.info("[StarletteErrorMiddleware] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        await self.app(scope, logging_receive, intercepting_send)


# Create the MCP server
mcp = FastMCP(
    name="Faulty MCP Server",
    instructions="A simple test server for reproducing MCP errors.",
    middleware=[LoggingMiddleware(include_payloads=True), McpErrorMiddleware()],
)


@mcp.tool
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@mcp.tool
def always_error() -> None:
    """Always throw an exception to simulate errors."""
    raise ValueError("Simulated error")


@mcp.tool
async def freeze_server(seconds: int = 60) -> str:
    """Simulate a server freeze for testing purposes."""
    await asyncio.sleep(seconds)
    return f"Server frozen for {seconds} seconds"


@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b


@mcp.tool
def random_throw_exception(a: float, b: float, prob: float = 0.5) -> float:
    """Randomly throw an exception to simulate errors."""
    if random() < prob:
        raise ValueError("Simulated error")
    return a * b


@mcp.tool
def throw_404_exception() -> None:
    """Randomly throw an exception to simulate errors."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Throwing a 404 error for testing purposes.")


def run_server_on_port():
    """Run a single MCP server using the global configuration."""

    async def run_async():
        print(f"[Port {config.port}] Starting MCP server on http://localhost:{config.port}/mcp/")
        await mcp.run_http_async(
            transport="streamable-http",
            host="localhost",
            port=config.port,
            path="/mcp/",
            middleware=[StarletteMiddleware(StarletteErrorMiddleware)],
        )

    asyncio.run(run_async())


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run a faulty MCP server for testing error handling")
    parser.add_argument(
        "--safe-mode",
        action="store_true",
        help="Set all error probabilities to 0 by default, only use explicitly provided values",
    )
    parser.add_argument(
        "--port",
        type=int,
        help=f"Port to run the server on (default: {config.port})",
    )
    parser.add_argument(
        "--prob-on-post-404",
        type=float,
        help=f"Probability of injecting a 404 error for POST requests (default: {config.prob_on_post_404})",
    )
    parser.add_argument(
        "--prob-on-get-crash",
        type=float,
        help=f"Probability of terminating on GET request (default: {config.prob_on_get_crash})",
    )
    parser.add_argument(
        "--prob-on-delete-404",
        type=float,
        help=f"Probability of injecting a 404 error for DELETE requests (default: {config.prob_on_delete_404})",
    )
    parser.add_argument(
        "--prob-in-list-tools-throw",
        type=float,
        help=f"Probability of exception in list tools handling (default: {config.prob_in_list_tools_throw})",
    )
    parser.add_argument(
        "--prob-in-list-tools-crash",
        type=float,
        help=f"Probability of terminating in list tools handling (default: {config.prob_in_list_tools_crash})",
    )

    args = parser.parse_args()

    def _update_config_value(attr_name: str):
        if args.safe_mode:
            setattr(config, attr_name, 0)
        if (given_value := getattr(args, attr_name)) is not None:
            setattr(config, attr_name, given_value)

    # Update the global configuration with command line arguments
    config.port = args.port or config.port
    _update_config_value("prob_on_post_404")
    _update_config_value("prob_on_get_crash")
    _update_config_value("prob_on_delete_404")
    _update_config_value("prob_in_list_tools_throw")
    _update_config_value("prob_in_list_tools_crash")

    # Run the server
    run_server_on_port()
