from collections.abc import Callable
from pathlib import Path

from aixtools.agents.context.data_models import FileExtractionResult, FileType
from aixtools.agents.context.processors.common import count_lines, create_error_result
from aixtools.agents.context.processors.text import detect_encoding, process_text
from aixtools.utils import config


def process_code(
    file_path: Path,
    start_line: int | None = None,
    end_line: int | None = None,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process code files with line range selection and truncation.

    Args:
        file_path: Path to code file
        start_line: Starting line index (0-based, inclusive). None = 0
        end_line: Ending line index (0-based, exclusive). None = start_line + MAX_LINES
        max_line_length: Maximum characters per line
        max_total_output: Maximum total output length
        tokenizer: Optional tokenizer function
    """
    result = process_text(
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        max_line_length=max_line_length,
        max_total_output=max_total_output,
        tokenizer=tokenizer,
    )

    if result.success:
        result.file_type = FileType.CODE

    return result


def process_code_head(
    file_path: Path,
    limit: int = config.MAX_LINES,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process first N lines of code file."""
    return process_code(
        file_path=file_path,
        start_line=0,
        end_line=limit,
        max_line_length=max_line_length,
        max_total_output=max_total_output,
        tokenizer=tokenizer,
    )


def process_code_tail(
    file_path: Path,
    limit: int = config.MAX_LINES,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process last N lines of code file."""
    try:
        encoding = detect_encoding(file_path)
        total_lines = count_lines(file_path, encoding)
        start = max(0, total_lines - limit)

        return process_code(
            file_path=file_path,
            start_line=start,
            end_line=total_lines,
            max_line_length=max_line_length,
            max_total_output=max_total_output,
            tokenizer=tokenizer,
        )
    except Exception as e:
        return create_error_result(e, FileType.CODE, file_path, "code file")
