"""
Pydantic models for logging system.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LogType(str, Enum):
    """Type of log entry."""

    COMMAND = "command"
    CODE = "code"
    SYSTEM = "system"
    SERVICE = "service"


class Language(str, Enum):
    """Programming language of the code."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SHELL = "shell"
    BASH = "bash"
    OTHER = "other"


class ProcessResult(BaseModel):
    """
    Process results from a command or code execution.
    Includes exit code, stdout, and stderr.
    """

    exit_code: int = Field(description="Exit code of the command or process")
    stdout: str = Field(description="Standard output of the command or process")
    stderr: str = Field(description="Standard error of the command or process")


class BaseLogEntry(BaseModel):
    """Base model for all log entries."""

    id: str = Field(description="Unique identifier for the log entry")
    user_id: str = Field(description="ID of the user who initiated the action")
    session_id: str = Field(description="ID of the session")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time when the log entry was created",
    )
    log_type: LogType = Field(description="Type of log entry")
    container_id: str | None = Field(None, description="ID of the container where the action was performed")


class CommandLogEntry(BaseLogEntry):
    """Log entry for shell command execution."""

    log_type: LogType = LogType.COMMAND
    command: str = Field(description="Shell command that was executed")
    working_directory: str = Field(description="Working directory where the command was executed")
    process_result: ProcessResult | None = Field(
        None,
        description="Process results: exit status, STDOUT, and STDERR from the command",
    )
    duration_ms: int | None = Field(None, description="Duration of command execution in milliseconds")


class CodeLogEntry(BaseLogEntry):
    """Log entry for code execution."""

    log_type: LogType = LogType.CODE
    language: Language = Field(description="Programming language of the code")
    code: str = Field(description="Code that was executed")
    file_path: str | None = Field(None, description="Path to the file where the code was saved")
    process_result: ProcessResult | None = Field(
        None,
        description="Process results: exit status, STDOUT, and STDERR from the command",
    )
    duration_ms: int | None = Field(None, description="Duration of code execution in milliseconds")


class SystemLogEntry(BaseLogEntry):
    """Log entry for system events."""

    log_type: LogType = LogType.SYSTEM
    event: str = Field(description="Description of the system event")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details about the event")


class ServiceLogEntry(BaseLogEntry):
    """Log entry for service events."""

    log_type: LogType = LogType.SERVICE
    service_id: str = Field(description="ID of the service")
    event: str = Field(description="Description of the service event")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details about the event")


# Union type for all log entry types
LogEntry = CommandLogEntry | CodeLogEntry | SystemLogEntry | ServiceLogEntry
