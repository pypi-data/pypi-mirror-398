"""
Utility functions for handling log files.
"""

from datetime import datetime
from pathlib import Path


def get_log_files(log_dir: Path) -> list[Path]:
    """Get all log files in the specified directory, sorted by modification time (newest first)."""
    if not log_dir.exists():
        return []
    log_files = list(log_dir.glob("agent_run.*.pkl"))
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return log_files


def format_timestamp_from_filename(filename: str) -> str:
    """Extract and format the timestamp from a log filename."""
    try:
        # Extract timestamp from format "agent_run.YYYYMMDD_HHMMSS.pkl"
        timestamp_str = filename.split("agent_run.")[1].split(".pkl")[0]
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    except (IndexError, ValueError):
        return "Unknown date"
