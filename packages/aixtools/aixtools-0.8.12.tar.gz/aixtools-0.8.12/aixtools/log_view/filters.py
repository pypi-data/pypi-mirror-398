"""
Functions for filtering nodes based on various criteria.
"""

import re
from typing import Any

from aixtools.log_view.node_summary import get_node_type


def filter_nodes(nodes: list, filters: dict[str, Any]) -> list:
    """Filter nodes based on multiple criteria."""
    if not filters:
        return nodes

    filtered_nodes = nodes.copy()

    # Apply text filter if provided
    if "text" in filters and filters["text"]:
        text_filter = filters["text"].lower()
        filtered_nodes = [node for node in filtered_nodes if text_filter in str(node).lower()]

    # Apply type filter if provided
    if "types" in filters and filters["types"]:
        filtered_nodes = [node for node in filtered_nodes if get_node_type(node) in filters["types"]]

    # Apply attribute filter if provided
    if "attribute" in filters and filters["attribute"]:
        attr_filter = filters["attribute"]
        filtered_nodes = [node for node in filtered_nodes if hasattr(node, "__dict__") and attr_filter in vars(node)]

    # Apply regex filter if provided
    if "regex" in filters and filters["regex"]:
        try:
            pattern = re.compile(filters["regex"], re.IGNORECASE)
            filtered_nodes = [node for node in filtered_nodes if pattern.search(str(node))]
        except re.error:
            # Invalid regex pattern, ignore this filter
            pass

    return filtered_nodes
