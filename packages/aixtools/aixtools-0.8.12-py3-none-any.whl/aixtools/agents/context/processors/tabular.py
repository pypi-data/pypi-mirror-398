import csv
import io
from collections.abc import Callable
from pathlib import Path

from aixtools.agents.context.data_models import FileExtractionResult, FileType, TruncationInfo
from aixtools.agents.context.processors.common import (
    check_and_apply_output_limit,
    create_error_result,
    create_file_metadata,
    format_truncation_summary,
    truncate_string,
)
from aixtools.utils import config


def _detect_delimiter(file_path: Path) -> str:
    """Detect delimiter (comma or tab) from file.

    Uses a small fixed sample size for fast detection, even on large files.
    """
    try:
        # Use fixed 8KB sample - sufficient for delimiter detection, fast on large files
        # Previously used 10% of file size which was extremely slow for large CSVs
        sample_size = 8192

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            sample = f.read(sample_size)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            return dialect.delimiter
    except Exception:
        if file_path.suffix.lower() == ".tsv":
            return "\t"
        return ","


def _read_header_and_count(file_path: Path, delimiter: str, count_rows: bool = True) -> tuple[list[str], int | None]:
    """Read CSV header and optionally count total rows.

    Args:
        file_path: Path to CSV file
        delimiter: CSV delimiter
        count_rows: If False, skip counting rows (returns None for total_rows)

    Returns:
        Tuple of (header, total_rows). total_rows is None if count_rows=False.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration:
            return [], 0

        # Skip expensive row counting for large files unless specifically needed
        if not count_rows:
            return header, None

        total_rows = sum(1 for _ in reader)
    return header, total_rows


def _read_row_range(
    file_path: Path, delimiter: str, start: int, end: int, max_row_bytes: int = 100000
) -> list[list[str]]:
    """Read rows from start to end index without loading entire file.

    Args:
        file_path: Path to CSV file
        delimiter: CSV delimiter
        start: Starting row index (0-based)
        end: Ending row index (exclusive)
        max_row_bytes: Maximum bytes to read per row before truncating (default: 100KB)

    Returns:
        List of rows. Very long rows (>max_row_bytes) are pre-truncated for performance.
    """
    selected_rows = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        # Read and parse header
        header_line = f.readline()
        # Parse full header (needed for column info)
        header_reader = csv.reader(io.StringIO(header_line), delimiter=delimiter)
        try:
            next(header_reader)  # Consume header from main file position
        except StopIteration:
            pass

        # Read data rows
        for i in range(end):
            line = f.readline()
            if not line:
                break

            # For very long rows (>max_row_bytes), truncate before CSV parsing
            # This prevents csv.reader from spending time parsing huge rows we'll truncate anyway
            if len(line) > max_row_bytes:
                line = line[:max_row_bytes] + "\n"

            if i >= start:
                # Parse the (possibly truncated) line
                row_reader = csv.reader(io.StringIO(line), delimiter=delimiter)
                try:
                    row = next(row_reader)
                    selected_rows.append(row)
                except (StopIteration, csv.Error):
                    # Handle malformed rows from truncation
                    selected_rows.append([f"[Row {i + 1} parsing error after truncation]"])

    return selected_rows


def _truncate_row(row: list[str], max_columns: int, max_cell_length: int) -> tuple[list[str], int]:
    """Truncate row to max columns and truncate each cell."""
    row_truncated = row[:max_columns]
    cells_truncated = 0

    truncated_row = []
    for cell in row_truncated:
        truncated_cell, was_truncated = truncate_string(cell, max_cell_length)
        truncated_row.append(truncated_cell)
        if was_truncated:
            cells_truncated += 1

    return truncated_row, cells_truncated


def _write_row_as_line(row: list[str], delimiter: str, max_line_length: int) -> str:
    """Convert row to CSV line and truncate if needed."""
    row_str = io.StringIO()
    temp_writer = csv.writer(row_str, delimiter=delimiter, lineterminator="")
    temp_writer.writerow(row)
    line = row_str.getvalue()

    if len(line) > max_line_length:
        line = line[:max_line_length] + "..."

    return line


def process_tabular(
    file_path: Path,
    start_row: int | None = None,
    end_row: int | None = None,
    max_cell_length: int = config.MAX_CELL_LENGTH,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_columns: int = config.MAX_COLUMNS,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process CSV/TSV files with row range selection and truncation.

    Args:
        file_path: Path to CSV/TSV file
        start_row: Starting row index (0-based, inclusive). None = 0. Negative values count from end.
        end_row: Ending row index (0-based, exclusive). None = start_row + 10
        max_cell_length: Maximum characters per cell
        max_line_length: Maximum characters per line
        max_columns: Maximum number of columns
        max_total_output: Maximum total output length
        tokenizer: Optional tokenizer function
    """
    try:
        # Extract file metadata
        metadata = create_file_metadata(file_path, encoding="utf-8")

        # Detect delimiter
        delimiter = _detect_delimiter(file_path)
        file_type = FileType.CSV

        # Only count rows if negative indexing is used (for tail functionality)
        # This avoids expensive iteration through entire file for large CSVs
        needs_row_count = start_row is not None and start_row < 0
        header, total_rows = _read_header_and_count(file_path, delimiter, count_rows=needs_row_count)

        # Calculate row range (default: 10 rows from start)
        # Handle negative indices for tail functionality
        if start_row is not None and start_row < 0:
            if total_rows is None:
                # Should not happen due to needs_row_count logic above, but be defensive
                header, total_rows = _read_header_and_count(file_path, delimiter, count_rows=True)
            actual_start = max(0, total_rows + start_row)
        else:
            actual_start = start_row if start_row is not None else 0

        actual_end = end_row if end_row is not None else actual_start + 10

        if not header:
            return FileExtractionResult(
                content="", success=True, file_type=file_type, truncation_info=TruncationInfo(), metadata=metadata
            )

        # Truncate columns
        total_columns = len(header)
        columns_to_show = min(total_columns, max_columns)
        header_truncated = header[:columns_to_show]

        # Read selected row range
        selected_rows = _read_row_range(file_path, delimiter, actual_start, actual_end)
        rows_shown = len(selected_rows)

        # Build output
        output = io.StringIO()

        csv_writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
        cells_truncated = 0

        # Write header with cell truncation
        truncated_header, header_cells_truncated = _truncate_row(header_truncated, columns_to_show, max_cell_length)
        cells_truncated += header_cells_truncated
        csv_writer.writerow(truncated_header)

        # Write data rows with truncation
        for row in selected_rows:
            truncated_row, row_cells_truncated = _truncate_row(row, columns_to_show, max_cell_length)
            cells_truncated += row_cells_truncated

            line = _write_row_as_line(truncated_row, delimiter, max_line_length)
            output.write(line + "\n")

            # Stop if exceeding total output limit
            if output.tell() > max_total_output:
                output.write("\n...\n")
                break

        # Build truncation info
        # If total_rows is None (not counted), show rows_shown without total
        if total_rows is None:
            rows_info = f"first {rows_shown} rows" if rows_shown > 0 else None
        else:
            rows_info = f"{rows_shown} of {total_rows}" if rows_shown < total_rows else None

        truncation_info = TruncationInfo(
            columns_shown=f"{columns_to_show} of {total_columns}" if total_columns > columns_to_show else None,
            rows_shown=rows_info,
            cells_truncated=cells_truncated,
            total_output_limit_reached=output.tell() > max_total_output,
        )

        if tokenizer:
            content_str = output.getvalue()
            truncation_info.tokens_shown = tokenizer(content_str)

        # Add truncation summary
        summary = format_truncation_summary(truncation_info)
        if summary:
            output.write(summary)

        # Final output with total length check
        result_content = check_and_apply_output_limit(output.getvalue(), max_total_output, truncation_info)

        return FileExtractionResult(
            content=result_content,
            success=True,
            file_type=file_type,
            truncation_info=truncation_info,
            metadata=metadata,
        )

    except Exception as e:
        return create_error_result(e, FileType.CSV, file_path, "tabular file")


def process_tabular_head(
    file_path: Path,
    limit: int = config.DEFAULT_ROWS_HEAD,
    max_cell_length: int = config.MAX_CELL_LENGTH,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_columns: int = config.MAX_COLUMNS,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process first N rows of CSV/TSV file."""
    return process_tabular(
        file_path=file_path,
        start_row=0,
        end_row=limit,
        max_cell_length=max_cell_length,
        max_line_length=max_line_length,
        max_columns=max_columns,
        max_total_output=max_total_output,
        tokenizer=tokenizer,
    )


def process_tabular_tail(
    file_path: Path,
    limit: int = config.DEFAULT_ROWS_TAIL,
    max_cell_length: int = config.MAX_CELL_LENGTH,
    max_line_length: int = config.MAX_LINE_LENGTH,
    max_columns: int = config.MAX_COLUMNS,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process last N rows of CSV/TSV file."""
    return process_tabular(
        file_path=file_path,
        start_row=-limit,
        end_row=None,
        max_cell_length=max_cell_length,
        max_line_length=max_line_length,
        max_columns=max_columns,
        max_total_output=max_total_output,
        tokenizer=tokenizer,
    )
