"""Middleware to extract and set A2A context from HTTP headers."""

from starlette.authentication import SimpleUser
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from aixtools.context import (
    HTTP_AUTHORIZATION_HEADER,
    HTTP_SESSION_ID_HEADER,
    HTTP_USER_ID_HEADER,
    auth_token_var,
    session_id_var,
    user_id_var,
)


class A2AContextMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """
    Middleware that extracts user-id and session-id from HTTP headers
    and stores them in context variables.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Extract session context from headers and set context variables.

        Args:
            request: The incoming HTTP request
            call_next: The next function in the middleware chain
        """
        user_id = request.headers.get(HTTP_USER_ID_HEADER)
        session_id = request.headers.get(HTTP_SESSION_ID_HEADER)
        auth_header = request.headers.get(HTTP_AUTHORIZATION_HEADER)

        if user_id:
            user_id_var.set(user_id)

        # override user_id from Authorization if present
        user = request.scope.get("user")
        if isinstance(user, SimpleUser):
            user_id_var.set(user.username)

        if session_id:
            session_id_var.set(session_id)
        if auth_header:
            if auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                auth_token_var.set(token)
            else:
                # Store the full header if it's not a Bearer token
                auth_token_var.set(auth_header)

        response = await call_next(request)
        return response
