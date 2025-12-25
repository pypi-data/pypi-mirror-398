"""Error handling middleware for MCP servers."""

import traceback

from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.middleware import MiddlewareContext

from aixtools.mcp.exceptions import AixToolError


class AixErrorHandlingMiddleware(ErrorHandlingMiddleware):
    """Custom middleware class for handling errors in MCP servers."""

    def log_as_warn_with_traceback(
        self, *, error: Exception, original_error: Exception, context: MiddlewareContext
    ) -> None:
        """Logs provided error as warning.
        original_error is an 'unwrapped' error if applicable, otherwise can be the same as error param.
        """
        error_type = type(original_error).__name__
        method = context.method or "unknown"
        error_key = f"{error_type}:{method}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        base_message = f"{method} resulted in {error_type}: {str(error)}"
        if self.include_traceback:
            self.logger.warning(f"{base_message}\n{traceback.format_exc()}")
        if self.error_callback:
            try:
                self.error_callback(error, context)
            except Exception as callback_error:  # pylint: disable=broad-exception-caught
                self.logger.warning("Callback failed spectacularly: %s", callback_error)

    def handle_error(self, error: Exception, context: MiddlewareContext) -> bool:
        """Custom error logging"""
        if isinstance(error, AixToolError):
            self.log_as_warn_with_traceback(error=error, original_error=error, context=context)
            return True

        inner_error = error
        while hasattr(inner_error, "__cause__") and inner_error.__cause__ is not None:
            inner_error = inner_error.__cause__
            if isinstance(inner_error, AixToolError):
                self.log_as_warn_with_traceback(error=error, original_error=inner_error, context=context)
                return True

        return False

    def _log_error(self, error: Exception, context: MiddlewareContext) -> None:
        """Override original _log_error method."""
        if self.handle_error(error, context):
            return
        super()._log_error(error, context)
