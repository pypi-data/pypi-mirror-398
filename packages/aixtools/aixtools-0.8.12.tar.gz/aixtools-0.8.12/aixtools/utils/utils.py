"""
General utility functions for string manipulation, logging, and data handling.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

DF_SHOW_MAX_ROWS = 20


def escape_newline(s, max_length: int = 300) -> str:
    """Escape newlines in a string."""
    s = str(s)
    ss = "\\n".join(s.split("\n"))
    if len(ss) <= max_length:
        return ss
    return "".join(ss[:max_length]) + "..."


def escape_backticks(s) -> str:
    """Escape backticks in a string."""
    s = f"{s}"
    return s.replace("`", "\\`")


def find_file(path: Path, glob="*.pdf"):
    """Recursively find all files matching the glob pattern in a directory"""
    yield from path.rglob(glob)


def is_multiline(s: str) -> bool:
    """Check if a string is multiline."""
    s = str(s).rstrip()
    return "\n" in s


def is_too_long(s: str, max_length: int = 200) -> bool:
    """Check if a string is too long."""
    s = str(s).rstrip()
    return len(s) > max_length


def prepend_all_lines(msg, prepend="\t", skip_first_line: bool = False) -> str:
    """Prepend all lines of a message with a prepend."""
    out = ""
    for i, line in enumerate(str(msg).split("\n")):
        if i == 0 and skip_first_line:
            out += f"{line}\n"
        else:
            out += f"{prepend}{line}\n"
    return out


def remove_quotes(s):
    """
    Remove all quotes (including triple backticks with language specifications) surrounding a string.

    This function strips the input string of all surrounding quotes, including single quotes, double quotes,
    backticks, and triple backticks with or without language specifications. It continues to remove quotes
    until none are left.

    Args:
        s (str): The input string potentially surrounded by quotes.

    Returns:
        str: The string with all surrounding quotes removed. If the input is None, returns None.
    """
    if s is None:
        return None
    s = str(s).strip()
    while (
        (s.startswith('"') and s.endswith('"'))
        or (s.startswith("'") and s.endswith("'"))
        or (s.startswith("`") and s.endswith("`"))
        or ("```" in s)
    ):
        if "```" in s:
            s = tripple_quote_strip(s)
        else:
            # Single quotes
            s = s[1:-1].strip()
        # Remove spaces
        s = s.strip()
    return s


def tabit(s, prefix="\t|") -> str:
    """Add a prefix to each line of a string for improved readability."""
    s = str(s)
    return prefix + s.replace("\n", f"\n{prefix}")


def to_json_pretty_print(obj) -> str:
    """Convert to a pretty-printed JSON string if possible."""
    if isinstance(obj, str):
        # Already a string, try to parse as JSON, then pretty print
        s = obj
        try:
            obj = json.loads(s)
            return json.dumps(obj, indent=2)
        except Exception as _:  # pylint: disable=broad-exception-caught
            # Not a JSON string, return as is
            return s
    # Not a string, convert to pretty JSON
    try:
        return json.dumps(obj, indent=2)
    except Exception as _:  # pylint: disable=broad-exception-caught
        # Fallback to str representation
        return str(obj)


def to_str(data) -> str:
    """Convert any data type to a readable string representation."""
    # Primitive values, just use str()
    if isinstance(data, str):
        return f"'{str}'"
    if isinstance(data, (bool, bytes, float, int)):
        return str(data)
    # Dataframes
    if isinstance(data, pd.DataFrame):
        if data.shape[0] > DF_SHOW_MAX_ROWS:
            return f"Showing only the first {DF_SHOW_MAX_ROWS} rows out of {data.shape[0]}:\n" + data.head(
                DF_SHOW_MAX_ROWS
            ).to_markdown(index=False)
        return data.to_markdown(index=False)
    # Use json for list, dict, etc.
    if isinstance(data, (dict, list, tuple)):
        return json.dumps(data, indent=2, default=str)
    return str(data)


def truncate(s: str, max_len=76, ellipsis="...") -> str:
    """Truncate a string to a maximum length, adding ellipsis if needed."""
    s = str(s)
    if len(s) > max_len:
        return s[: max_len - len(ellipsis)] + ellipsis
    return s


def tripple_quote_strip(s):
    """
    Remove triple quotes from a string, including those with language specifications.

    Eexamples:
        ```sql SELECT * from table;```

        ```Here is your code ```python c = a + b ``` This code will perform addition```

    Args:
        s (str): The input string potentially containing triple quotes.

    Returns:
        str: The string with triple quotes removed, if present.
    """
    if "```" not in s:
        return s
    left_pos, right_pos = len(s), s.rfind("```")
    s_lower = s.lower()
    pre_matched = ""
    for lang in ["python3", "python2", "python", "bash", "json", "sql", ""]:
        pre = f"```{lang}"
        idx = s_lower.find(pre)
        if idx != -1 and idx < left_pos:
            left_pos = idx
            pre_matched = pre
    if left_pos < right_pos:
        s = s[left_pos + len(pre_matched) : right_pos].strip()
    return s


def timestamp_with_uuid() -> str:
    """Get a timestamp string + a UUID string (first 8 chars)."""
    (yyy, hh, uu) = timestamp_uuid_tuple()
    return f"{yyy}.{hh}.{uu[:8]}"


def timestamp_uuid_tuple() -> tuple[str, str, str]:
    """
    Get a tuple of timestamp + a UUID: (YYYY-MM-DD, HH:MM:SS, UUID)
    """
    now = datetime.now()
    return (now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), str(uuid.uuid4()))


def str2bool(v: str | None) -> bool:
    """Convert a string to a boolean value."""
    if not v:
        return False
    return str(v).lower() in ("yes", "true", "on", "1")


async def async_iter(items):
    """Asynchronously iterate over items."""
    for item in items:
        yield item
