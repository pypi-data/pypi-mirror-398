"""
OpenTelemetry integration for logging and tracing agent operations.
"""

import os

import logfire  # pylint: disable=import-error
from pydantic_ai import Agent

from aixtools.utils.config import LOGFIRE_TOKEN, LOGFIRE_TRACES_ENDPOINT


def open_telemetry_on():
    """Configure and enable OpenTelemetry tracing with LogFire integration."""
    service_name = "agent_poc"

    if LOGFIRE_TRACES_ENDPOINT:
        os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = LOGFIRE_TRACES_ENDPOINT
        logfire.configure(
            service_name=service_name,
            # Sending to Logfire is on by default regardless of the OTEL env vars.
            # Keep this line here if you don't want to send to both Jaeger and Logfire.
            send_to_logfire=False,
        )
        Agent.instrument_all(True)
        return

    if LOGFIRE_TOKEN:
        logfire.configure(
            token=LOGFIRE_TOKEN,
            service_name=service_name,
        )
        Agent.instrument_all(True)
        return

    print("OpenTelemetry is not enabled. Set the LOGFIRE_TOKEN or LOGFIRE_TRACES_ENDPOINT environment variable.")
