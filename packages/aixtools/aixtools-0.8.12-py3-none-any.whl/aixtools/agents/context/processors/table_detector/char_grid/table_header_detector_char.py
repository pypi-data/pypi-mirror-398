"""Header detection for character grid table analysis."""

from aixtools.agents.context.processors.table_detector.table_region import TableRegion
from aixtools.agents.context.processors.table_detector.worksheet_as_char import WorksheetAsChar


class TableHeaderDetectorChar:
    """Detects header rows in table regions using character grid analysis.

    This detector identifies cases where the table's actual header row is NOT the first row
    of the detected table region. This happens when:
    - The table has title rows or metadata rows before the header
    - Sparse leading rows are diagonally connected to the main table via connectivity algorithm
    - The table starts with numeric or mixed-type rows before the actual header

    The detector analyzes candidate rows within a table bounding box to identify the true
    header row by scoring each candidate. If a clear header is found (score > min_header_score),
    it sets header_row explicitly and adjusts start_row. If no clear header is found, header_row
    remains None and the first row (start_row) is used as the header by default.

    Scoring algorithm:
    - Text ratio (configurable weight, default 60%): Proportion of string characters in row
    - Following data score (configurable weight, default 40%): Binary score if next row has dense data
    - Column jump bonus (configurable max, default 50%): Bonus when current row has 2x+ columns vs previous

    The row with highest score above the minimum threshold becomes the adjusted start_row and
    is explicitly marked as header_row.
    """

    def __init__(
        self,
        char_grid: WorksheetAsChar,
        header_candidate_limit: int = 10,
        min_candidate_cols: int = 2,
        min_header_score: float = 0.3,
        text_ratio_weight: float = 0.6,
        following_data_weight: float = 0.4,
        max_column_jump_bonus: float = 0.5,
    ):
        """Initialize header detector with character grid and parameters.

        Args:
            char_grid: Character grid representation of worksheet
            header_candidate_limit: Maximum number of rows to analyze
            min_candidate_cols: Minimum non-space cells for a row to be candidate
            min_header_score: Minimum score required to accept a row as header
            text_ratio_weight: Weight for text ratio in score calculation
            following_data_weight: Weight for following data in score calculation
            max_column_jump_bonus: Maximum bonus when columns jump significantly
        """
        self.char_grid = char_grid
        self.header_candidate_limit = header_candidate_limit
        self.min_candidate_cols = min_candidate_cols
        self.min_header_score = min_header_score
        self.text_ratio_weight = text_ratio_weight
        self.following_data_weight = following_data_weight
        self.max_column_jump_bonus = max_column_jump_bonus

    def adjust_table_start_row(self, table: TableRegion) -> TableRegion | None:
        """Adjust table start row to actual header position by analyzing candidate rows.

        This method identifies when the first row of the detected table is NOT the actual header.
        It analyzes up to header_candidate_limit rows (default 10) from the table start, scoring
        each candidate to find the true header row.

        If a clear header is found (score > min_header_score, default 0.3), returns a new TableRegion
        with adjusted start_row and explicit header_row set. If no clear header is found, returns the
        original table unchanged (header_row remains None, and first row will be used as header by default).
        """
        start_row_0idx = table.start_row - 1
        end_row_0idx = table.end_row - 1
        start_col_0idx = table.start_col - 1
        end_col_0idx = table.end_col - 1

        if end_row_0idx - start_row_0idx < 1:
            return table

        candidate_rows = self._get_candidate_rows(start_row_0idx, end_row_0idx, start_col_0idx, end_col_0idx)
        if len(candidate_rows) < 2:
            return table

        best_header_row = self._find_best_header(candidate_rows, end_row_0idx, start_col_0idx, end_col_0idx)

        if best_header_row is not None:
            return TableRegion(
                sheet_name=table.sheet_name,
                start_row=best_header_row + 1,
                end_row=table.end_row,
                start_col=table.start_col,
                end_col=table.end_col,
                header_row=best_header_row + 1,
                worksheet=table.worksheet,
            )

        return table

    def _get_candidate_rows(
        self, start_row_0idx: int, end_row_0idx: int, start_col_0idx: int, end_col_0idx: int
    ) -> list[tuple[int, int, str]]:
        """Extract candidate rows with sufficient non-space cells."""
        candidate_rows = []
        for row_idx in range(start_row_0idx, min(start_row_0idx + self.header_candidate_limit, end_row_0idx + 1)):
            if row_idx >= len(self.char_grid):
                break
            line = self.char_grid[row_idx]
            row_chars = line[start_col_0idx : end_col_0idx + 1] if start_col_0idx < len(line) else ""
            non_space_count = sum(1 for c in row_chars if c != " ")
            if non_space_count >= self.min_candidate_cols:
                candidate_rows.append((row_idx, non_space_count, row_chars))
        return candidate_rows

    def _find_best_header(
        self, candidate_rows: list[tuple[int, int, str]], end_row_0idx: int, start_col_0idx: int, end_col_0idx: int
    ) -> int | None:
        """Find the best header row by scoring candidates."""
        best_header_row = None
        best_score = 0.0
        prev_col_count = None

        for row_idx, col_count, row_chars in candidate_rows:
            score = self._calculate_header_score(
                row_idx, col_count, row_chars, end_row_0idx, start_col_0idx, end_col_0idx, prev_col_count
            )
            if score > best_score:
                best_score = score
                best_header_row = row_idx
            prev_col_count = col_count

        return best_header_row if best_score > self.min_header_score else None

    def _calculate_header_score(
        self,
        row_idx: int,
        col_count: int,
        row_chars: str,
        end_row_0idx: int,
        start_col_0idx: int,
        end_col_0idx: int,
        prev_col_count: int | None,
    ) -> float:
        """Calculate score for a candidate header row.

        Scoring components:
        - Text ratio: Proportion of string characters ('s') in the row
        - Following data score: Binary score if next row has min_candidate_cols+ non-space cells
        - Column jump bonus: When current row has 2x+ columns vs previous row
        """
        text_count = sum(1 for c in row_chars if c == "s")
        text_ratio = text_count / col_count if col_count > 0 else 0

        following_data_score = self._calculate_following_data_score(row_idx, end_row_0idx, start_col_0idx, end_col_0idx)
        column_jump_bonus = self._calculate_column_jump_bonus(col_count, prev_col_count)

        score = (
            text_ratio * self.text_ratio_weight + following_data_score * self.following_data_weight + column_jump_bonus
        )
        return score

    def _calculate_following_data_score(
        self, row_idx: int, end_row_0idx: int, start_col_0idx: int, end_col_0idx: int
    ) -> float:
        """Calculate score based on whether next row has dense data."""
        next_row_idx = row_idx + 1
        if next_row_idx <= end_row_0idx and next_row_idx < len(self.char_grid):
            next_line = self.char_grid[next_row_idx]
            next_row_chars = next_line[start_col_0idx : end_col_0idx + 1] if start_col_0idx < len(next_line) else ""
            next_non_space = sum(1 for c in next_row_chars if c != " ")
            return 1.0 if next_non_space >= self.min_candidate_cols else 0.0
        return 0.0

    def _calculate_column_jump_bonus(self, col_count: int, prev_col_count: int | None) -> float:
        """Calculate bonus when columns jump significantly from previous row."""
        if prev_col_count is not None and prev_col_count > 0:
            column_ratio = col_count / prev_col_count
            if column_ratio >= 2.0:
                return min((column_ratio - 1.0) / 3.0, self.max_column_jump_bonus)
        return 0.0
