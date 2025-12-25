"""
Utilities for truncating text and data structures while preserving readability.

These utilities are used across MCP servers to prevent large responses from
saturating LLM context while still providing useful previews.
"""

import io
import json
from typing import TypeVar

import pandas as pd
from pydantic import BaseModel


class TruncationMetadata(BaseModel):
    """Metadata about truncation operation."""

    original_size: int
    truncated_size: int
    was_truncated: bool
    strategy: str  # "none", "smart", "middle", "str"


# TypeVar for preserving input type through truncate_recursive_obj
T = TypeVar("T")


def truncate_text_head_tail(text: str, head_chars: int, tail_chars: int) -> tuple[str, int]:
    """Truncate text keeping head and tail portions.

    Args:
        text: Text to truncate
        head_chars: Number of characters to keep from start
        tail_chars: Number of characters to keep from end

    Returns:
        Tuple of (truncated_text, chars_removed)

    Example:
        >>> truncate_text_head_tail("Hello World!", 5, 3)
        ('Hello\n... +1 chars ...\nrld!', 1)
    """
    if len(text) <= head_chars + tail_chars:
        return text, 0

    head = text[:head_chars]
    tail = text[-tail_chars:] if tail_chars > 0 else ""

    chars_removed = len(text) - head_chars - len(tail)

    if tail:
        truncated = f"{head}\n... +{chars_removed} chars ...\n{tail}"
    else:
        truncated = f"{head}\n... +{chars_removed} chars ..."

    return truncated, chars_removed


def truncate_text_middle(text: str, max_chars: int) -> tuple[str, int]:
    """Truncate text in the middle, keeping start and end.

    Args:
        text: Text to truncate
        max_chars: Maximum total characters (including ellipsis)

    Returns:
        Tuple of (truncated_text, chars_removed)

    Example:
        >>> truncate_text_middle("Hello World!", 10)
        ('Hel...rld!', 2)
    """
    if len(text) <= max_chars:
        return text, 0

    # Reserve 3 chars for "..."
    available = max_chars - 3
    half = available // 2

    truncated = text[:half] + "..." + text[-half:]
    chars_removed = len(text) - max_chars

    return truncated, chars_removed


def format_truncation_message(
    original_size: int,
    truncated_size: int,
    unit: str = "chars",
    file_path: str | None = None,
    recommendation: str | None = None,
) -> str:
    """Generate a standard truncation warning message.

    Args:
        original_size: Original size before truncation
        truncated_size: Size after truncation
        unit: Unit of measurement ("chars", "tokens", "rows")
        file_path: Optional path where full content was saved
        recommendation: Optional recommendation for user

    Returns:
        Formatted truncation message

    Example:
        >>> format_truncation_message(10000, 2000, "chars", "/workspace/data.csv")
        'Content truncated from 10000 to 2000 chars.\\nFull content saved to /workspace/data.csv'
    """
    parts = [f"Content truncated from {original_size:,} to {truncated_size:,} {unit}."]

    if file_path:
        parts.append(f"Full content saved to {file_path}")

    if recommendation:
        parts.append(f"Recommendation: {recommendation}")

    return "\n".join(parts)


def truncate_df_to_csv(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches,too-many-statements
    df: pd.DataFrame,
    max_cell_chars: int = 80,
    max_row_chars: int = 2000,
    max_rows: int | None = None,
    max_columns: int | None = None,
    max_total_length: int | None = None,
    file_path: str | None = None,
) -> str:
    """Convert DataFrame to CSV with comprehensive truncation.

    Applies multiple levels of truncation to ensure the output is concise:
    1. Truncates rows (head+tail), columns (left+right), and cell contents
    2. Truncates CSV lines to max_row_chars
    3. Optionally limits total output length to max_total_length
    4. Includes informative truncation messages

    Args:
        df: DataFrame to convert
        max_cell_chars: Maximum characters per cell (default: 80)
        max_row_chars: Maximum characters per CSV line (default: 2000)
        max_rows: Maximum rows to include (split between head/tail), None for all
        max_columns: Maximum columns to include (split between left/right), None for all
        max_total_length: Maximum total output length, None for no limit
        file_path: Optional file path to include in truncation messages (e.g., where full data was saved)

    Returns:
        CSV string with all truncation applied and informative messages

    Example:
        >>> df = pd.DataFrame({"col1": ["x" * 200] * 100, "col2": range(100)})
        >>> csv = truncate_df_to_csv(df, max_rows=10, max_cell_chars=50, file_path="results.csv")
    """
    if df.empty:
        return df.to_csv(index=False)

    original_rows = len(df)
    original_cols = len(df.columns)
    total_rows, total_cols = df.shape

    # Add file header if data was saved
    file_header = ""
    if file_path:
        file_header = f"Full results ({original_rows} rows) saved to `{file_path}`\n\n"

    # Apply row truncation (head + tail)
    rows_message = ""
    if max_rows is not None and total_rows > max_rows:
        top = max_rows // 2
        bottom = max_rows - top
        df_truncated = pd.concat(
            [
                df.head(top),
                pd.DataFrame([["..."] * total_cols], columns=df.columns),
                df.tail(bottom),
            ],
            ignore_index=True,
        )
        rows_message = format_truncation_message(
            original_size=original_rows, truncated_size=max_rows, unit="rows", file_path=file_path
        )
    else:
        df_truncated = df.copy()

    # Apply column truncation (left + right)
    columns_message = ""
    if max_columns is not None and total_cols > max_columns:
        left = max_columns // 2
        right = max_columns - left
        df_truncated = df_truncated[[*df.columns[:left], *df.columns[-right:]]]
        df_truncated.insert(left, "...", ["..."] * df_truncated.shape[0])
        columns_message = format_truncation_message(
            original_size=original_cols, truncated_size=max_columns, unit="columns", file_path=file_path
        )

    # Truncate cell contents
    for col in df_truncated.columns:
        df_truncated[col] = df_truncated[col].apply(
            lambda x: str(x)[:max_cell_chars] + "..." if isinstance(x, str) and len(str(x)) > max_cell_chars else x
        )

    # Convert to CSV
    csv_buffer = io.StringIO()
    df_truncated.to_csv(csv_buffer, index=False, lineterminator="\n")
    csv_output = csv_buffer.getvalue()

    # Truncate lines that exceed max_row_chars
    lines = csv_output.split("\n")
    truncated_lines = []
    for line in lines:
        if len(line) > max_row_chars:
            truncated_lines.append(line[:max_row_chars] + "...")
        else:
            truncated_lines.append(line)

    # Combine result with messages
    result = "\n".join(truncated_lines)
    if rows_message:
        result = rows_message + "\n\n" + result
    if columns_message:
        result += "\n" + columns_message
    if file_header:
        result = file_header + result

    # Apply total length limit if specified
    if max_total_length is not None and len(result) > max_total_length:
        result = result[:max_total_length] + "..."

    return result


def truncate_recursive_obj(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-return-statements,too-many-branches,too-many-statements
    obj: T,
    max_string_len: int | None = None,
    max_list_len: int | None = None,
    max_dict_keys: int | None = None,
    target_size: int | None = None,
    ensure_size: bool = False,
    return_metadata: bool = False,
) -> T | tuple[T, TruncationMetadata]:
    """Recursively truncate a JSON-serializable object while preserving structure.

    This function intelligently truncates nested data structures by:
    - Truncating long strings in the middle
    - Showing head + tail items for long lists
    - Showing head + tail keys for large dicts

    Args:
        obj: Object to truncate (dict, list, str, or primitive).
             Caller must convert custom objects to dict before calling.
        max_string_len: Maximum length for string values (default 60, or calculated from target_size)
        max_list_len: Maximum number of list items to show (default 20, or calculated from target_size)
        max_dict_keys: Maximum number of dict keys to show (default 20, or calculated from target_size)
        target_size: If provided, auto-calculate parameters based on target output size in chars
        ensure_size: If True, validate JSON-serialized result fits within target_size and apply
                    fallback truncation if needed. Requires target_size to be set.
        return_metadata: If True, return (result, metadata) tuple with truncation details

    Returns:
        Truncated version of the object with same type as input, or (result, TruncationMetadata)
        tuple if return_metadata=True. The return type matches the input type.

    Examples:
        >>> # Explicit parameters - returns dict
        >>> data = {"items": [f"item_{i}" for i in range(100)], "description": "A" * 1000}
        >>> truncated = truncate_recursive_obj(data, max_string_len=60, max_list_len=10)

        >>> # Auto-calculated from target size - returns dict
        >>> truncated = truncate_recursive_obj(data, target_size=1000)

        >>> # With size validation and metadata - returns tuple[dict, TruncationMetadata]
        >>> result, meta = truncate_recursive_obj(data, target_size=1000, ensure_size=True, return_metadata=True)
        >>> if meta.was_truncated:
        ...     print(f"Truncated from {meta.original_size} to {meta.truncated_size}")
    """
    # Validate ensure_size requirements
    if ensure_size and target_size is None:
        raise ValueError("ensure_size=True requires target_size to be set")

    # Initialize metadata if needed
    metadata = TruncationMetadata(
        original_size=0,
        truncated_size=0,
        was_truncated=False,
        strategy="none",
    )

    # Track if we encounter non-serializable objects
    had_non_serializable = False

    # Capture original size if we need to track truncation
    if ensure_size or return_metadata:
        try:
            original_serialized = json.dumps(obj, ensure_ascii=False)
            metadata.original_size = len(original_serialized)
        except (TypeError, ValueError):
            # Can't serialize - mark as having non-serializable content
            # This will be treated as truncated since we'll convert to string
            had_non_serializable = True

    # Handle strings first (before parameter calculation)
    if isinstance(obj, str):
        if max_string_len is None:
            max_string_len = max(20, target_size // 20) if target_size else 60
        truncated, _ = truncate_text_middle(obj, max_string_len)

        if return_metadata:
            return truncated, TruncationMetadata(
                original_size=len(obj),
                truncated_size=len(truncated),
                was_truncated=len(obj) > max_string_len,
                strategy="smart" if len(obj) > max_string_len else "none",
            )
        return truncated

    # Calculate parameters from target_size if provided
    if target_size is not None:
        max_string_len = max_string_len or max(20, target_size // 20)
        max_list_len = max_list_len or max(5, target_size // 100)
        max_dict_keys = max_dict_keys or max(5, target_size // 50)
    else:
        # Apply defaults if still None
        max_string_len = max_string_len or 60
        max_list_len = max_list_len or 20
        max_dict_keys = max_dict_keys or 20

    # Handle lists
    if isinstance(obj, list):
        if len(obj) > max_list_len:
            head = obj[: max_list_len // 2]
            tail = obj[-max_list_len // 2 :]
            result = [
                *[truncate_recursive_obj(x, max_string_len, max_list_len, max_dict_keys) for x in head],
                "...",
                *[truncate_recursive_obj(x, max_string_len, max_list_len, max_dict_keys) for x in tail],
            ]
        else:
            result = [truncate_recursive_obj(item, max_string_len, max_list_len, max_dict_keys) for item in obj]

    # Handle dicts
    elif isinstance(obj, dict):
        keys = list(obj.keys())
        if len(keys) > max_dict_keys:
            head = keys[: max_dict_keys // 2]
            tail = keys[-max_dict_keys // 2 :]
            result = {k: truncate_recursive_obj(obj[k], max_string_len, max_list_len, max_dict_keys) for k in head}
            result["..."] = "..."
            for k in tail:
                result[k] = truncate_recursive_obj(obj[k], max_string_len, max_list_len, max_dict_keys)
        else:
            result = {k: truncate_recursive_obj(v, max_string_len, max_list_len, max_dict_keys) for k, v in obj.items()}

    # Handle primitives
    elif isinstance(obj, (int, float, bool, type(None))):
        result = obj
    else:
        # Unknown type - convert to string representation
        result = str(obj)
        # Truncate if needed
        if max_string_len and len(result) > max_string_len:
            result, _ = truncate_text_middle(result, max_string_len)

    # If not ensure_size, return result (possibly with metadata)
    if not ensure_size:
        if return_metadata:
            try:
                serialized = json.dumps(result, ensure_ascii=False)
                metadata.original_size = len(serialized)
                metadata.truncated_size = len(serialized)
            except (TypeError, ValueError):
                str_result = str(result)
                metadata.original_size = len(str_result)
                metadata.truncated_size = len(str_result)
            return result, metadata
        return result

    # ensure_size=True: validate JSON size and apply fallback if needed
    # Try to serialize the truncated result
    try:
        serialized = json.dumps(result, ensure_ascii=False)
        # Update original_size if not captured earlier
        if metadata.original_size == 0:
            metadata.original_size = len(serialized)

        if len(serialized) <= target_size:
            metadata.truncated_size = len(serialized)
            metadata.strategy = "smart"
            # Check if truncation actually occurred
            if metadata.original_size > target_size or had_non_serializable:
                metadata.was_truncated = True
            if return_metadata:
                return result, metadata
            return result

        # Result still too large - try with indent=2
        serialized_pretty = json.dumps(result, indent=2, ensure_ascii=False)
        if len(serialized_pretty) <= target_size:
            metadata.truncated_size = len(serialized_pretty)
            metadata.was_truncated = True
            metadata.strategy = "smart"
            if return_metadata:
                return serialized_pretty, metadata
            return serialized_pretty

        # Still too large - use middle truncation as fallback
        truncated, _ = truncate_text_middle(serialized, target_size - 100)
        metadata.truncated_size = len(truncated)
        metadata.was_truncated = True
        metadata.strategy = "middle"
        if return_metadata:
            return truncated, metadata
        return truncated

    except (TypeError, ValueError):
        # JSON serialization failed - fallback to string truncation
        str_result = str(result)
        metadata.original_size = len(str_result)

        if len(str_result) <= target_size:
            metadata.truncated_size = len(str_result)
            metadata.strategy = "str"
            if return_metadata:
                return str_result, metadata
            return str_result

        truncated, _ = truncate_text_middle(str_result, target_size - 50)
        metadata.truncated_size = len(truncated)
        metadata.was_truncated = True
        metadata.strategy = "middle"
        if return_metadata:
            return truncated, metadata
        return truncated
