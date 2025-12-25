import io
import json
from collections.abc import Callable
from pathlib import Path

from aixtools.agents.context.data_models import FileExtractionResult, FileType, TruncationInfo
from aixtools.agents.context.processors.common import (
    check_and_apply_output_limit,
    create_error_result,
    create_file_metadata,
    format_truncation_summary,
    human_readable_size,
    truncate_string,
)
from aixtools.utils import config


def _truncate_structure(
    data: dict | list | str | int | float | bool | None,
    current_depth: int,
    max_depth: int,
    max_array_items: int,
    max_object_keys: int,
    max_string_length: int,
    max_object_string_length: int,
    truncation_stats: dict,
) -> dict | list | str | int | float | bool | None:
    """Recursively truncate nested structures with limits."""

    if current_depth > max_depth:
        truncation_stats["depth_truncations"] += 1
        return "... [max depth reached]"

    if isinstance(data, dict):
        keys = list(data.keys())
        truncated_dict = {}

        for i, key in enumerate(keys[:max_object_keys]):
            value = data[key]
            truncated_value = _truncate_structure(
                value,
                current_depth + 1,
                max_depth,
                max_array_items,
                max_object_keys,
                max_string_length,
                max_object_string_length,
                truncation_stats,
            )
            truncated_dict[key] = truncated_value

            dict_str = json.dumps(truncated_dict, ensure_ascii=False)
            if len(dict_str) > max_object_string_length:
                truncation_stats["object_length_truncations"] += 1
                if i > 0:
                    del truncated_dict[key]
                truncated_dict["..."] = f"[truncated {len(keys) - i} more keys]"
                break

        if len(keys) > max_object_keys:
            truncation_stats["object_truncations"] += 1
            truncated_dict["..."] = f"[{len(keys) - max_object_keys} more keys]"

        return truncated_dict

    elif isinstance(data, list):
        truncated_list = []

        for i, item in enumerate(data[:max_array_items]):
            truncated_item = _truncate_structure(
                item,
                current_depth + 1,
                max_depth,
                max_array_items,
                max_object_keys,
                max_string_length,
                max_object_string_length,
                truncation_stats,
            )
            truncated_list.append(truncated_item)

        if len(data) > max_array_items:
            truncation_stats["array_truncations"] += 1
            truncated_list.append(f"... [{len(data) - max_array_items} more items]")

        return truncated_list

    elif isinstance(data, str):
        truncated, was_truncated = truncate_string(data, max_string_length)
        if was_truncated:
            truncation_stats["string_truncations"] += 1
        return truncated

    else:
        return data


def _format_json_truncation_stats(truncation_stats: dict) -> dict:
    """Convert JSON truncation stats to format for common function."""
    extra_stats = {}
    if truncation_stats["array_truncations"] > 0:
        extra_stats["arrays"] = truncation_stats["array_truncations"]
    if truncation_stats["object_truncations"] > 0:
        extra_stats["objects"] = truncation_stats["object_truncations"]
    if truncation_stats["object_length_truncations"] > 0:
        extra_stats["large objects"] = truncation_stats["object_length_truncations"]
    if truncation_stats["string_truncations"] > 0:
        extra_stats["strings"] = truncation_stats["string_truncations"]
    if truncation_stats["depth_truncations"] > 0:
        extra_stats["deep structures"] = truncation_stats["depth_truncations"]
    return extra_stats


def process_json(
    file_path: Path,
    max_depth: int = config.MAX_NESTING_DEPTH,
    max_array_items: int = config.MAX_ARRAY_ITEMS,
    max_object_keys: int = config.MAX_OBJECT_KEYS,
    max_string_length: int = config.MAX_STRING_VALUE_LENGTH,
    max_object_string_length: int = config.MAX_OBJECT_STRING_LENGTH,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process JSON files with structure truncation."""
    try:
        metadata = create_file_metadata(file_path, mime_type="application/json")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        truncation_stats = {
            "array_truncations": 0,
            "object_truncations": 0,
            "object_length_truncations": 0,
            "string_truncations": 0,
            "depth_truncations": 0,
        }

        truncated_data = _truncate_structure(
            data,
            0,
            max_depth,
            max_array_items,
            max_object_keys,
            max_string_length,
            max_object_string_length,
            truncation_stats,
        )

        output = io.StringIO()
        output.write(f"File: {file_path.name}\n")
        output.write(f"Size: {human_readable_size(metadata.size_bytes)}\n\n")
        output.write("<content>\n")

        json_str = json.dumps(truncated_data, indent=2, ensure_ascii=False)
        output.write(json_str)
        output.write("\n</content>\n")

        truncation_info = TruncationInfo()

        if tokenizer:
            truncation_info.tokens_shown = tokenizer(output.getvalue())

        result_content = check_and_apply_output_limit(output.getvalue(), max_total_output, truncation_info)

        extra_stats = _format_json_truncation_stats(truncation_stats)
        summary = format_truncation_summary(truncation_info, extra_stats)
        if summary:
            result_content += summary

        return FileExtractionResult(
            content=result_content,
            success=True,
            file_type=FileType.JSON,
            truncation_info=truncation_info,
            metadata=metadata,
        )

    except json.JSONDecodeError as e:
        return create_error_result(e, FileType.JSON, file_path, "JSON (invalid JSON)")
    except Exception as e:
        return create_error_result(e, FileType.JSON, file_path, "JSON")
