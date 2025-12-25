"""
Functions for exporting nodes to various formats.
"""

import json


def export_nodes_to_json(nodes: list) -> str:
    """Export nodes to a JSON string for download."""
    # Convert nodes to a serializable format
    serializable_nodes = []

    for node in nodes:
        if hasattr(node, "__dict__"):
            # For objects with attributes
            node_dict = {
                "type": type(node).__name__,
                "attributes": {
                    attr: str(value) if not isinstance(value, (dict, list, int, float, bool, type(None))) else value
                    for attr, value in vars(node).items()
                    if not attr.startswith("_")
                },
            }
            serializable_nodes.append(node_dict)
        elif isinstance(node, dict):
            # For dictionaries
            serializable_nodes.append(
                {
                    "type": "dict",
                    "content": {
                        str(k): str(v) if not isinstance(v, (dict, list, int, float, bool, type(None))) else v
                        for k, v in node.items()
                    },
                }
            )
        elif isinstance(node, (list, tuple)):
            # For lists and tuples
            serializable_nodes.append(
                {
                    "type": "list" if isinstance(node, list) else "tuple",
                    "content": [
                        str(item) if not isinstance(item, (dict, list, int, float, bool, type(None))) else item
                        for item in node
                    ],
                }
            )
        else:
            # For primitive types
            serializable_nodes.append({"type": type(node).__name__, "value": str(node)})

    return json.dumps(serializable_nodes, indent=2)
