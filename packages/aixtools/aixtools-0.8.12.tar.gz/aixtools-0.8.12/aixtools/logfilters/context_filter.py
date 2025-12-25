"""
A logging filter for injecting contextual information into log records.
"""

import logging


class ContextFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    """
    A logging filter that injects a formatted context string (user and session
    IDs) into the log record. It sources the IDs from the active FastMCP
    application context and ignores default values.
    """

    def _extract_from_mcp_context(self) -> tuple[str | None, str | None]:
        """
        Retrieve session id (aka conversation id) and user id from the MCP context.
        Useful in MCP servers.
        """
        try:
            from aixtools.server.utils import (  # noqa: PLC0415 # pylint: disable=import-outside-toplevel
                get_session_id_tuple,
            )

            return get_session_id_tuple()
        except (ImportError, RuntimeError, ValueError):
            # Context is not available
            return None, None

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Adds a `context` string to the log record.

        The filter attempts to extract user, session (conversation) IDs from
        context variables. If that fails, it falls back to extracting IDs from
        the FastMCP context.

        If valid IDs are found, the `context` attribute is formatted as
        `[conversation:id user:id]`. Otherwise, it is an empty string.
        """
        user_id = None
        session_id = None

        try:
            # First, try to get context from the global context variables
            from aixtools.context import (  # noqa: PLC0415 # pylint: disable=import-outside-toplevel
                session_id_var,
                user_id_var,
            )

            user_id = user_id_var.get()
            session_id = session_id_var.get()
        except ImportError:
            pass

        mcp_user_id = None
        mcp_session_id = None
        if not user_id or not session_id:
            mcp_user_id, mcp_session_id = self._extract_from_mcp_context()

        user_id = user_id or mcp_user_id
        session_id = session_id or mcp_session_id

        context = ""
        if session_id and not str(session_id).startswith("default"):
            context += f"[{session_id}]"
        if user_id and not str(user_id).startswith("default"):
            context += f"[{user_id}]"

        record.context = context

        return True
