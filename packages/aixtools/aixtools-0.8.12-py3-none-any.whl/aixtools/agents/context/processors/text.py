import io
from collections.abc import Callable
from pathlib import Path

from aixtools.agents.context.data_models import FileExtractionResult, FileType, TruncationInfo
from aixtools.agents.context.processors.common import (
    check_and_apply_output_limit,
    count_lines,
    create_error_result,
    create_file_metadata,
    truncate_string,
)
from aixtools.utils import config


def detect_encoding(file_path: Path) -> str:
    """Detect file encoding with fallback strategy."""
    encodings = ["utf-8", "latin-1"]

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                f.read(1024)
            return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue

    return "latin-1"


def _read_line_range(file_path: Path, encoding: str, start: int, end: int) -> tuple[list[str], bool, bool]:
    """Read lines from start to end index without loading entire file.

    Returns:
        Tuple of (selected_lines, ended_at_eof, file_ends_with_newline)
    """
    selected_lines = []
    ended_at_eof = True
    last_line_had_newline = False

    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        for i, line in enumerate(f):
            if i >= start and i < end:
                selected_lines.append(line.rstrip("\n\r"))
                last_line_had_newline = line.endswith(("\n", "\r"))
            if i >= end:
                ended_at_eof = False
                break

    return selected_lines, ended_at_eof, last_line_had_newline


def process_text(
    file_path: Path,
    start_line: int | None = None,
    end_line: int | None = None,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
    file_type: FileType = FileType.TEXT,
) -> FileExtractionResult:
    """Process text files with line range selection and truncation.

    Args:
        file_path: Path to text file
        start_line: Starting line index (0-based, inclusive). None = 0
        end_line: Ending line index (0-based, exclusive). None = start_line + MAX_LINES
        max_line_length: Maximum characters per line
        max_total_output: Maximum total output length
        tokenizer: Optional tokenizer function
        file_type: File type to set in result (TEXT or MARKDOWN)
    """
    try:
        encoding = detect_encoding(file_path)
        metadata = create_file_metadata(file_path, encoding=encoding)

        # Calculate line range
        actual_start = start_line if start_line is not None else 0
        actual_end = end_line if end_line is not None else actual_start + config.MAX_LINES

        # Count total lines
        total_lines = count_lines(file_path, encoding)

        if total_lines == 0:
            return FileExtractionResult(
                content="", success=True, file_type=file_type, truncation_info=TruncationInfo(), metadata=metadata
            )

        # Read selected line range
        selected_lines, ended_at_eof, file_ends_with_newline = _read_line_range(
            file_path, encoding, actual_start, actual_end
        )
        lines_shown = len(selected_lines)

        # Build output
        output = io.StringIO()

        lines_truncated = 0
        for i, line in enumerate(selected_lines):
            truncated_line, was_truncated = truncate_string(line, max_line_length)

            if was_truncated:
                lines_truncated += 1

            if i > 0:
                output.write("\n")
            output.write(truncated_line)

            # Stop if exceeding total output limit
            if output.tell() > max_total_output:
                output.write("\n...")
                break

        # Add trailing newline if we read to EOF and file originally ended with newline
        if ended_at_eof and selected_lines and file_ends_with_newline:
            output.write("\n")

        # Build truncation info
        truncation_info = TruncationInfo(
            lines_shown=f"{lines_shown} of {total_lines}" if lines_shown < total_lines else None,
            total_output_limit_reached=output.tell() > max_total_output,
        )

        if tokenizer:
            content_str = output.getvalue()
            truncation_info.tokens_shown = tokenizer(content_str)

        # Final output with length check
        result_content = check_and_apply_output_limit(output.getvalue(), max_total_output, truncation_info)

        return FileExtractionResult(
            content=result_content,
            success=True,
            file_type=file_type,
            truncation_info=truncation_info,
            metadata=metadata,
        )

    except Exception as e:
        return create_error_result(e, FileType.TEXT, file_path, "text file")


def process_text_head(
    file_path: Path,
    limit: int = config.MAX_LINES,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process first N lines of text file."""
    return process_text(
        file_path=file_path,
        start_line=0,
        end_line=limit,
        max_line_length=max_line_length,
        max_total_output=max_total_output,
        tokenizer=tokenizer,
    )


def process_text_tail(
    file_path: Path,
    limit: int = config.MAX_LINES,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process last N lines of text file."""
    try:
        encoding = detect_encoding(file_path)
        total_lines = count_lines(file_path, encoding)
        start = max(0, total_lines - limit)

        return process_text(
            file_path=file_path,
            start_line=start,
            end_line=total_lines,
            max_line_length=max_line_length,
            max_total_output=max_total_output,
            tokenizer=tokenizer,
        )
    except Exception as e:
        return create_error_result(e, FileType.TEXT, file_path, "text file")
