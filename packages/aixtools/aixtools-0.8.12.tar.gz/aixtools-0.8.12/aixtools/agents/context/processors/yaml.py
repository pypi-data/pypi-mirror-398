import io
from collections.abc import Callable
from pathlib import Path

import yaml

from aixtools.agents.context.data_models import FileExtractionResult, FileType, TruncationInfo
from aixtools.agents.context.processors.common import (
    check_and_apply_output_limit,
    create_error_result,
    create_file_metadata,
    format_truncation_summary,
    human_readable_size,
)
from aixtools.agents.context.processors.json import _format_json_truncation_stats, _truncate_structure
from aixtools.utils import config


def process_yaml(
    file_path: Path,
    max_depth: int = config.MAX_NESTING_DEPTH,
    max_array_items: int = config.MAX_ARRAY_ITEMS,
    max_object_keys: int = config.MAX_OBJECT_KEYS,
    max_string_length: int = config.MAX_STRING_VALUE_LENGTH,
    max_object_string_length: int = config.MAX_OBJECT_STRING_LENGTH,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process YAML files with structure truncation."""
    try:
        metadata = create_file_metadata(file_path, mime_type="application/x-yaml")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

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

        yaml_str = yaml.dump(truncated_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        output.write(yaml_str)
        output.write("</content>\n")

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
            file_type=FileType.YAML,
            truncation_info=truncation_info,
            metadata=metadata,
        )

    except yaml.YAMLError as e:
        return create_error_result(e, FileType.YAML, file_path, "YAML (invalid YAML)")
    except Exception as e:
        return create_error_result(e, FileType.YAML, file_path, "YAML")
