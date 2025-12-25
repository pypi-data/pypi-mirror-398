"""Abstract base class for table detectors."""

from abc import ABC, abstractmethod

from openpyxl.workbook import Workbook

from aixtools.agents.context.processors.table_detector.table_region import TableRegion


class TableDetectorBase(ABC):
    """Base class for table detection algorithms."""

    def __init__(
        self,
        workbook: Workbook,
        min_rows: int = 2,
        min_cols: int = 2,
        min_data_density: float = 0.3,
        header_candidate_limit: int = 10,
        min_candidate_cols: int = 2,
        min_header_score: float = 0.3,
        text_ratio_weight: float = 0.6,
        following_data_weight: float = 0.4,
        max_column_jump_bonus: float = 0.5,
    ):
        """Initialize detector with configurable thresholds.

        Args:
            workbook: The workbook containing the sheets to analyze
            min_rows: Minimum rows for a valid table
            min_cols: Minimum columns for a valid table
            min_data_density: Minimum ratio of non-None cells (0.0-1.0)
            header_candidate_limit: Maximum number of rows to analyze for header detection
            min_candidate_cols: Minimum non-space cells for a row to be header candidate
            min_header_score: Minimum score required to accept a row as header
            text_ratio_weight: Weight for text ratio in header score calculation
            following_data_weight: Weight for following data in header score calculation
            max_column_jump_bonus: Maximum bonus when columns jump significantly
        """
        self.workbook = workbook
        self.min_rows = min_rows
        self.min_cols = min_cols
        self.min_data_density = min_data_density
        self.header_candidate_limit = header_candidate_limit
        self.min_candidate_cols = min_candidate_cols
        self.min_header_score = min_header_score
        self.text_ratio_weight = text_ratio_weight
        self.following_data_weight = following_data_weight
        self.max_column_jump_bonus = max_column_jump_bonus

    def detect(self) -> list[TableRegion]:
        """Detect all table regions in all worksheets of the workbook."""
        all_tables = []
        for sheet in self.workbook.worksheets:
            tables = self._detect_tables(sheet)
            all_tables.extend(tables)
        return all_tables

    @abstractmethod
    def _detect_tables(self, sheet) -> list[TableRegion]:
        """Detect all table regions in all worksheets of the workbook."""
        pass

    def _get_occupied_cells(self, rows_data: list[tuple]) -> set[tuple[int, int]]:
        """Get set of (row, col) coordinates that contain non-None values."""
        occupied = set()
        for row_idx, row in enumerate(rows_data):
            for col_idx, cell in enumerate(row):
                if cell is not None and str(cell).strip():
                    occupied.add((row_idx, col_idx))
        return occupied

    def _is_valid_table(self, table: TableRegion) -> bool:
        """Validate if detected region qualifies as a table."""
        num_rows = table.end_row - table.start_row + 1
        num_cols = table.end_col - table.start_col + 1

        if num_rows < self.min_rows or num_cols < self.min_cols:
            return False

        if table.worksheet is None:
            return False

        total_cells = num_rows * num_cols
        non_none_cells = 0
        for row_idx in range(table.start_row, table.end_row + 1):
            for col_idx in range(table.start_col, table.end_col + 1):
                cell = table.worksheet.cell(row_idx, col_idx)
                if cell.value is not None:
                    non_none_cells += 1

        density = non_none_cells / total_cells if total_cells > 0 else 0

        return density >= self.min_data_density
