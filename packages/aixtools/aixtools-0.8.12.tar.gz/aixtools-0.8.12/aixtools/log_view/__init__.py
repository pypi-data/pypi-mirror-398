"""
Streamlit application to visualize agent nodes from log files.

This package provides tools to:
- View the most recent log file by default
- Open and analyze other log files
- Visualize nodes from agent runs with expandable/collapsible sections
- Filter nodes by various criteria
- Export visualizations
"""

from aixtools.log_view.app import main, main_cli

__all__ = [
    "main",
    "main_cli",
]
