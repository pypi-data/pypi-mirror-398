"""Custom exceptions for MCP services."""


class AixToolError(Exception):
    """Retryable tool error. Raise this when a tool fails but the operation should be retried."""
