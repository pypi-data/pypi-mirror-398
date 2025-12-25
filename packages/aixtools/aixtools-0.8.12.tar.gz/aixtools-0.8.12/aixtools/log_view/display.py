"""
Functions for displaying nodes in the Streamlit interface.
Provides enhanced display capabilities for various object types,
including dataclasses, with proper handling of nested structures.
"""

import inspect
import json
from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass

import pandas as pd
import streamlit as st
from rich.console import Console

from aixtools.utils.utils import prepend_all_lines

# Toggle for using markdown display instead of JSON
USE_MARKDOWN = True


def filter_private_fields(data_dict: dict) -> dict:
    """Filter out private fields from the data dictionary."""
    return {k: v for k, v in data_dict.items() if not k.startswith("_")}


def filter_private_attributes(obj) -> dict:
    """
    Filter out private attributes and methods from an object.
    Returns a dictionary of public attributes and their values.
    """
    if not hasattr(obj, "__dict__"):
        return {}

    result = {}
    for attr, value in vars(obj).items():
        if not attr.startswith("_"):
            result[attr] = value

    return result


def is_method(obj, attr_name: str) -> bool:
    """Check if an attribute is a method."""
    try:
        attr = getattr(obj, attr_name)
        return inspect.ismethod(attr) or inspect.isfunction(attr)
    except (AttributeError, TypeError):
        return False


def get_object_type_str(obj) -> str:  # noqa: PLR0911, pylint: disable=too-many-return-statements
    """Get a string representation of the object's type."""
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "bool"
    if isinstance(obj, int):
        return "int"
    if isinstance(obj, float):
        return "float"
    if isinstance(obj, str):
        return "str"
    if isinstance(obj, list):
        return f"list[{len(obj)}]"
    if isinstance(obj, tuple):
        return f"tuple[{len(obj)}]"
    if isinstance(obj, dict):
        return f"dict[{len(obj)}]"
    if isinstance(obj, set):
        return f"set[{len(obj)}]"
    if is_dataclass(obj):
        return f"dataclass:{type(obj).__name__}"
    if hasattr(obj, "__dict__"):
        return type(obj).__name__

    return type(obj).__name__


def object_to_json_with_types(obj, max_depth: int = 5, current_depth: int = 0):  # noqa: PLR0911, PLR0912, pylint: disable=too-many-return-statements,too-many-branches
    """
    Convert an object to a JSON-serializable dictionary with type information.
    Handles nested objects up to max_depth.
    """
    # Prevent infinite recursion
    if current_depth > max_depth:
        return {"__type": get_object_type_str(obj), "__value": str(obj)}

    # Handle None
    if obj is None:
        return None

    # Handle basic types
    if isinstance(obj, (bool, int, float, str)):
        return obj

    # Handle lists and tuples
    if isinstance(obj, (list, tuple)):
        items = []
        for item in obj:
            items.append(object_to_json_with_types(item, max_depth, current_depth + 1))
        return items

    # Handle dictionaries
    if isinstance(obj, dict):
        result = {}
        for key, value in filter_private_fields(obj).items():
            result[key] = object_to_json_with_types(value, max_depth, current_depth + 1)
        return result

    # Handle sets
    if isinstance(obj, set):
        items = []
        for item in obj:
            items.append(object_to_json_with_types(item, max_depth, current_depth + 1))
        return {"__type": "set", "__items": items}

    # Handle dataclasses
    if is_dataclass(obj):
        result = {"__type": f"dataclass:{type(obj).__name__}"}
        for field in dataclass_fields(obj):
            if field.name.startswith("_"):  # Skip private fields
                continue
            if not hasattr(obj, field.name):  # Skip not found
                continue
            value = getattr(obj, field.name)
            result[field.name] = object_to_json_with_types(value, max_depth, current_depth + 1)
        return result

    # Handle objects with __dict__
    if hasattr(obj, "__dict__"):
        result = {"__type": type(obj).__name__}
        for attr, value in filter_private_attributes(obj).items():
            if not is_method(obj, attr):  # Skip methods
                result[attr] = object_to_json_with_types(value, max_depth, current_depth + 1)
        return result

    # Handle other types
    return {"__type": get_object_type_str(obj), "__value": str(obj)}


def object_to_markdown(  # noqa: PLR0911, PLR0912, PLR0915, pylint: disable=too-many-locals,too-many-return-statements,too-many-branches,too-many-statements
    obj, max_depth: int = 5, current_depth: int = 0, indent: str = ""
) -> str:
    """
    Convert an object to a compact markdown representation.
    Handles nested objects up to max_depth.
    """
    max_display_items = 10  # Show only first MAX_DISPLAY_ITEMS items for large collections, dicts, and sets

    # Prevent infinite recursion
    if current_depth > max_depth:
        return f"`{get_object_type_str(obj)}`: {str(obj)}"

    # Handle None
    if obj is None:
        return "`None`"

    # Handle basic types
    if isinstance(obj, bool):
        return f"`{str(obj).lower()}`"

    if isinstance(obj, (int, float)):
        return f"`{obj}`"

    if isinstance(obj, str):
        lines = str(obj).splitlines()
        if len(lines) > 1:
            return f"\n{indent}```\n{prepend_all_lines(obj, prepend=indent)}\n{indent}```\n"
        return obj

    # Handle lists and tuples
    if isinstance(obj, (list, tuple)):
        if not obj:  # Empty collection
            return f"`{get_object_type_str(obj)}`: empty"

        max_inline_length = 3  # For small collections, show inline
        if (
            len(obj) <= max_inline_length
            and current_depth > 0
            and all(isinstance(x, (bool, int, float, str, type(None))) for x in obj)
        ):
            items = [object_to_markdown(item, max_depth, current_depth + 1) for item in obj]
            return f"`{get_object_type_str(obj)}`: [{', '.join(items)}]"

        # For larger collections, use bullet points
        result = [f"`{get_object_type_str(obj)}`:"]
        for i, item in enumerate(obj):
            if i >= max_display_items and len(obj) > max_display_items + 2:
                result.append(f"{indent}* ... ({len(obj) - 10} more items)")
                break
            item_md = object_to_markdown(item, max_depth, current_depth + 1, indent + "  ")
            result.append(f"{indent}* {item_md}")
        return "\n".join(result)

    # Handle dictionaries
    if isinstance(obj, dict):
        if not obj:  # Empty dict
            return "`dict`: empty"

        result = [f"`dict[{len(obj)}]`:"]
        for i, (key, value) in enumerate(filter_private_fields(obj).items()):
            if i >= max_display_items and len(obj) > max_display_items + 2:
                result.append(f"{indent}* ... ({len(obj) - 10} more items)")
                break
            value_md = object_to_markdown(value, max_depth, current_depth + 1, indent + "  ")
            result.append(f"{indent}* **{key}**: {value_md}")
        return "\n".join(result)

    # Handle sets
    if isinstance(obj, set):
        if not obj:  # Empty set
            return "`set`: empty"

        result = [f"`set[{len(obj)}]`:"]
        for i, item in enumerate(obj):
            if i >= max_display_items and len(obj) > max_display_items + 2:
                result.append(f"{indent}* ... ({len(obj) - 10} more items)")
                break
            item_md = object_to_markdown(item, max_depth, current_depth + 1, indent + "  ")
            result.append(f"{indent}* {item_md}")
        return "\n".join(result)

    # Handle dataclasses
    if is_dataclass(obj):
        result = [f"`{type(obj).__name__}:`"]
        for field in dataclass_fields(obj):
            if field.name.startswith("_"):  # Skip private fields
                continue
            if not hasattr(obj, field.name):  # Skip not found
                continue
            value = getattr(obj, field.name)
            value_md = object_to_markdown(value, max_depth, current_depth + 1, indent + "  ")
            result.append(f"{indent}* **{field.name}**: {value_md}")
        return "\n".join(result)

    # Handle objects with __dict__
    if hasattr(obj, "__dict__"):
        attrs = filter_private_attributes(obj)
        if not attrs:  # No public attributes
            return f"`{type(obj).__name__}`: (no public attributes)"

        result = [f"`{type(obj).__name__}`:"]
        for attr, value in attrs.items():
            if not is_method(obj, attr):  # Skip methods
                value_md = object_to_markdown(value, max_depth, current_depth + 1, indent + "  ")
                result.append(f"{indent}* **{attr}**: {value_md}")
        return "\n".join(result)

    # Handle other types
    return f"`{get_object_type_str(obj)}`: {str(obj)}"


def format_json_for_display(json_obj) -> str:
    """Format a JSON object for display with proper indentation."""
    return json.dumps(json_obj, indent=2, default=str)


def display_node(node, display_format: str) -> None:
    """
    Display node content based on its type, with enhanced formatting.
    """
    # Special handling for specific types
    if isinstance(node, pd.DataFrame):
        st.dataframe(node)
        return

    # Toggle between markdown and JSON display
    match display_format:
        case "Markdown":
            st.markdown(object_to_markdown(node))
        case "JSON":
            st.json(object_to_json_with_types(node))
        case "Rich":
            st.write(rich_print(node))
        case _:
            raise ValueError(f"Unsupported display format: {display_format}")


def rich_print(node):
    """Display a node using rich print."""
    console = Console(color_system=None)
    with console.capture() as capture:
        console.print(node)
    return f"```\n{capture.get()}\n```"
