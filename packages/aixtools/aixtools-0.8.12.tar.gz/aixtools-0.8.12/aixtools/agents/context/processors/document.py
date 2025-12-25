import hashlib
import io
from collections.abc import Callable
from pathlib import Path

from markitdown import MarkItDown

from aixtools.agents.context.data_models import FileExtractionResult, FileType, TruncationInfo
from aixtools.agents.context.processors.common import (
    check_and_apply_output_limit,
    create_error_result,
    create_file_metadata,
    truncate_string,
)
from aixtools.utils import config


def _get_cache_path(file_path: Path) -> Path:
    """Generate cache file path for markdown conversion."""
    file_hash = hashlib.md5(f"{file_path}:{file_path.stat().st_mtime}".encode()).hexdigest()
    cache_dir = file_path.parent / ".markitdown_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f"{file_path.stem}_{file_hash}.md"


def _get_cached_markdown(file_path: Path) -> str | None:
    """Retrieve cached markdown conversion if available."""
    cache_path = _get_cache_path(file_path)
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    return None


def _save_markdown_cache(file_path: Path, markdown_content: str) -> None:
    """Save markdown conversion to cache."""
    cache_path = _get_cache_path(file_path)
    cache_path.write_text(markdown_content, encoding="utf-8")


def _convert_to_markdown(file_path: Path) -> str:
    """Convert document to markdown using markitdown."""
    markitdown = MarkItDown()
    result = markitdown.convert(str(file_path))
    return result.text_content


def _truncate_markdown_lines(
    markdown_content: str, max_lines: int, max_line_length: int, max_total_output: int
) -> tuple[str, int]:
    """Truncate markdown content by lines."""
    lines = markdown_content.split("\n")
    output = io.StringIO()
    lines_truncated = 0

    for i, line in enumerate(lines[:max_lines]):
        truncated_line, was_truncated = truncate_string(line, max_line_length)
        if was_truncated:
            lines_truncated += 1

        output.write(f"{truncated_line}\n")

        if output.tell() > max_total_output:
            output.write("...\n")
            break

    return output.getvalue(), lines_truncated


def process_document(
    file_path: Path,
    file_type: FileType,
    max_lines: int = config.MAX_LINES,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    use_cache: bool = True,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process document files (PDF, DOCX) with markdown conversion and caching.

    Args:
        file_path: Path to document file
        file_type: Already-detected file type (PDF or DOCX)
        max_lines: Maximum number of lines to show
        max_line_length: Maximum characters per line
        max_total_output: Maximum total output length
        use_cache: Use cached conversion if available
        tokenizer: Optional tokenizer function
    """
    try:
        metadata = create_file_metadata(file_path, mime_type=f"document/{file_path.suffix[1:]}")

        if use_cache:
            markdown_content = _get_cached_markdown(file_path)
            if not markdown_content:
                markdown_content = _convert_to_markdown(file_path)
                _save_markdown_cache(file_path, markdown_content)
        else:
            markdown_content = _convert_to_markdown(file_path)

        lines = markdown_content.split("\n")
        total_lines = len(lines)
        lines_shown = min(max_lines, total_lines)

        truncated_content, _ = _truncate_markdown_lines(markdown_content, max_lines, max_line_length, max_total_output)

        truncation_info = TruncationInfo(
            lines_shown=f"{lines_shown} of {total_lines}" if lines_shown < total_lines else None,
            total_output_limit_reached=len(truncated_content) > max_total_output,
        )

        if tokenizer:
            truncation_info.tokens_shown = tokenizer(truncated_content)

        result_content = check_and_apply_output_limit(truncated_content, max_total_output, truncation_info)

        return FileExtractionResult(
            content=result_content,
            success=True,
            was_extracted=True,
            file_type=file_type,
            truncation_info=truncation_info,
            metadata=metadata,
        )

    except Exception as e:
        return create_error_result(e, file_type, file_path, "document")


def process_document_head(
    file_path: Path,
    file_type: FileType,
    limit: int = config.MAX_LINES,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    use_cache: bool = True,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process first N lines of document file."""
    return process_document(
        file_path=file_path,
        file_type=file_type,
        max_lines=limit,
        max_line_length=max_line_length,
        max_total_output=max_total_output,
        use_cache=use_cache,
        tokenizer=tokenizer,
    )
