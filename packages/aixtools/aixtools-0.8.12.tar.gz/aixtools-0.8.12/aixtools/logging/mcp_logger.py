"""
Logger implementations for MCP server.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from aixtools.logging.logging_config import get_logger

from .mcp_log_models import CodeLogEntry, CommandLogEntry, LogEntry, ServiceLogEntry, SystemLogEntry

logger = get_logger(__name__)


def log_with_default_logger(entry: LogEntry) -> None:
    """
    Formats a log entry into a human-readable string and logs it.
    """
    if isinstance(entry, SystemLogEntry):
        logger.info("%s: %s", entry.event, entry.details or "")
    elif isinstance(entry, ServiceLogEntry):
        logger.info("%s: %s", entry.event, entry.details or "")
    elif isinstance(entry, CodeLogEntry):
        logger.info("%s code: %s", entry.language, entry.code)
    elif isinstance(entry, CommandLogEntry):
        logger.info("%s, CWD: %s", entry.command, entry.working_directory)
    else:
        logger.debug("Logging entry: %s", entry.model_dump_json(indent=2))


class McpLogger(ABC):
    """Abstract base class for loggers."""

    @abstractmethod
    def log(self, entry: LogEntry) -> None:
        """Log an entry."""

    @abstractmethod
    def get_logs(  # noqa: PLR0913  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        container_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        """Get logs with optional filters."""


class JSONFileMcpLogger(McpLogger):
    """Logger that stores logs in a single JSON file."""

    def __init__(self, log_dir: str | Path):
        """Initialize the logger."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file_path = self.log_dir / "mcp_logs.jsonl"
        self.log_file = open(self.log_file_path, "a", encoding="utf-8")  # pylint: disable=consider-using-with

    def __del__(self):
        """Ensure file is closed when the logger is destroyed."""
        if hasattr(self, "log_file") and self.log_file and not self.log_file.closed:
            self.log_file.close()

    def _get_log_file_path(self) -> Path:
        """Get the path to the log file."""
        return self.log_file_path

    def log(self, entry: LogEntry) -> None:
        """Log an entry to the JSON file."""
        log_with_default_logger(entry)
        # Convert the entry to a JSON string
        entry_json = entry.model_dump_json()
        # Append the entry to the log file and flush to ensure it's written
        self.log_file.write(entry_json + "\n")
        self.log_file.flush()

    def get_logs(  # noqa: PLR0913, PLR0912  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-branches
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        container_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        """Get logs with optional filters.

        Args:
            user_id: Filter by user ID.
            session_id: Filter by session ID.
            container_id: Filter by container ID.
            start_time: Filter by start time.
            end_time: Filter by end time.
            limit: Maximum number of logs to return.

        Returns:
            List of log entries.
        """
        logs: list[LogEntry] = []

        # Ensure any pending writes are flushed to disk
        self.log_file.flush()

        # Read from the single log file
        if self.log_file_path.exists():
            with open(self.log_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        # Parse the JSON entry
                        entry_dict = json.loads(line)

                        # Convert timestamp string to datetime
                        entry_dict["timestamp"] = datetime.fromisoformat(entry_dict["timestamp"])

                        # Apply filters
                        if user_id and entry_dict.get("user_id") != user_id:
                            continue
                        if session_id and entry_dict.get("session_id") != session_id:
                            continue
                        if container_id and entry_dict.get("container_id") != container_id:
                            continue
                        if start_time and entry_dict["timestamp"] < start_time:
                            continue
                        if end_time and entry_dict["timestamp"] > end_time:
                            continue

                        # Create the appropriate log entry object based on log_type
                        log_type = entry_dict["log_type"]
                        if log_type == "command":
                            entry = CommandLogEntry(**entry_dict)
                        elif log_type == "code":
                            entry = CodeLogEntry(**entry_dict)
                        elif log_type == "system":
                            entry = SystemLogEntry(**entry_dict)
                        else:
                            continue

                        logs.append(entry)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error("Error parsing log entry: %s", e)
                        continue

                    # Check if we've reached the limit
                    if len(logs) >= limit:
                        break

        # Sort logs by timestamp (newest first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        return logs[:limit]


# Global logger instance
_mcp_logger: McpLogger | None = None


def initialize_mcp_logger(mcp_logger: McpLogger) -> None:
    """Initialize the MCP logger"""
    global _mcp_logger  # noqa: PLW0603, pylint: disable=global-statement
    _mcp_logger = mcp_logger


def get_mcp_logger() -> McpLogger:
    """Get the global logger for MCP server."""
    if _mcp_logger is None:
        raise RuntimeError("Logger not initialized")

    return _mcp_logger
