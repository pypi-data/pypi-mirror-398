"""Utilities for parsing MCP server capabilities from instructions."""

import json
import re
from typing import Any

CAPABILITY_START = "__CAPABILITIES__"
CAPABILITY_END = "__END_CAPABILITIES__"


def parse_capabilities(instructions: str | None) -> dict[str, Any] | None:
    """
    Parse capability announcement from MCP server instructions.

    Looks for JSON between __CAPABILITIES__ and __END_CAPABILITIES__ markers.
    Returns None if no capabilities found or parsing fails.

    Args:
        instructions: The instructions string from MCP initialize response

    Returns:
        Parsed capabilities dict or None

    Example:
        >>> instructions = '''
        ... __CAPABILITIES__
        ... {"features": ["google_search", "deep_research"]}
        ... __END_CAPABILITIES__
        ... This server provides...
        ... '''
        >>> caps = parse_capabilities(instructions)
        >>> caps["features"]
        ['google_search', 'deep_research']
    """
    if not instructions:
        return None

    try:
        # Find capability block
        pattern = f"{re.escape(CAPABILITY_START)}\\s*(.+?)\\s*{re.escape(CAPABILITY_END)}"
        match = re.search(pattern, instructions, re.DOTALL)

        if not match:
            return None

        # Parse JSON
        capabilities_json = match.group(1).strip()
        capabilities = json.loads(capabilities_json)

        # Validate required fields
        if not isinstance(capabilities, dict) or "features" not in capabilities:
            return None

        return capabilities

    except (json.JSONDecodeError, AttributeError):
        return None


def get_features(capabilities: dict[str, Any] | None) -> list[str]:
    """
    Extract feature list from capabilities dict.

    Args:
        capabilities: Parsed capabilities dict

    Returns:
        List of feature identifiers, empty list if none found

    Example:
        >>> caps = {"features": ["google_search", "deep_research"]}
        >>> get_features(caps)
        ['google_search', 'deep_research']
    """
    if not capabilities:
        return []
    return capabilities.get("features", [])


def build_instructions_with_capabilities(
    features: list[str],
    instructions: str,
    version: str = "1.0",
    metadata: dict[str, Any] | None = None,
) -> str:
    """
    Build MCP server instructions with embedded capability announcement.

    This helper function ensures capabilities are formatted correctly according
    to the MCP capability announcement specification.

    Args:
        features: List of feature identifiers (e.g., ["google_search", "deep_research"])
        instructions: Human-readable server instructions
        version: Capability schema version (default: "1.0")
        metadata: Optional additional metadata to include in capabilities

    Returns:
        Complete instructions string with embedded capability announcement

    Example:
        >>> instructions = build_instructions_with_capabilities(
        ...     features=["google_search", "deep_research"],
        ...     instructions="This server provides web research capabilities."
        ... )
        >>> print(instructions)
        __CAPABILITIES__
        {
          "features": [
            "google_search",
            "deep_research"
          ],
          "version": "1.0"
        }
        __END_CAPABILITIES__
        <BLANKLINE>
        This server provides web research capabilities.
    """
    # Build capabilities dict
    capabilities = {"features": features, "version": version}

    # Add metadata if provided
    if metadata:
        capabilities["metadata"] = metadata

    # Format JSON with indentation for readability
    capabilities_json = json.dumps(capabilities, indent=2)

    # Build complete instructions with capability block
    return f"{CAPABILITY_START}\n{capabilities_json}\n{CAPABILITY_END}\n\n{instructions}"
