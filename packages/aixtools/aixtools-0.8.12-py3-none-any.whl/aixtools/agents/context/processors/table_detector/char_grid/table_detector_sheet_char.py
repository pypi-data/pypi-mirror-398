"""Table detector for individual worksheets based on character grid representation."""

from openpyxl.worksheet.worksheet import Worksheet

from aixtools.agents.context.processors.table_detector.char_grid.table_header_detector_char import (
    TableHeaderDetectorChar,
)
from aixtools.agents.context.processors.table_detector.table_region import TableRegion
from aixtools.agents.context.processors.table_detector.worksheet_as_char import WorksheetAsChar


class TableDetectorSheetCharGrid:
    """Detect tables in a single worksheet using character grid representation.

    Algorithm operates in 5 stages:

    Stage 1 - Character Grid Conversion: The worksheet is converted to a character grid where
    each cell becomes a single character (s=string, i=int, f=float, d=date, b=bool, ?=other,
    space=empty). This simplified representation makes pattern analysis faster.

    Stage 2 - Occupied Cell Identification: Scans grid line-by-line, stores non-space positions
    as (row_idx, col_idx) tuples.

    Stage 3 - Row-Span-Based Connected Components: Groups cells by row, calculates column span
    (min to max column with data) for each row. Adjacent rows are considered connected if their
    column spans overlap (even partially). Uses flood-fill on row connectivity graph to find
    components. Handles tables with sparse rows that have large horizontal gaps within the same
    row (which would break traditional 8-directional flood-fill). Limits connectivity to rows
    at most 1 row apart (max_row_gap=1).

    Stage 4 - Header Detection: For each component, TableHeaderDetectorChar analyzes first 10
    candidate rows. Each row is scored based on:
    - Text ratio (60%): Proportion of string characters in the row
    - Following data score (40%): Binary score if next row has dense data (2+ non-space cells)
    - Column jump bonus (up to 50%): When current row has 2x+ columns vs previous row
    Row with highest score (minimum 0.3) becomes the header row and adjusts start_row.

    Stage 5 - Validation and Filtering: Validates tables against min_rows, min_cols,
    min_data_density requirements. Filters out small tables that are less than 10% the size
    of the largest table (likely metadata or titles).
    """

    def __init__(
        self,
        worksheet: Worksheet | None,
        worksheet_as_chargrid: WorksheetAsChar | None = None,
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
        """Initialize detector with worksheet.

        Args:
            worksheet: The worksheet to analyze
            worksheet_as_chargrid: Optional precomputed character grid representation (for testing)
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
        self.worksheet = worksheet
        self.min_rows = min_rows
        self.min_cols = min_cols
        self.min_data_density = min_data_density
        self.header_candidate_limit = header_candidate_limit
        self.min_candidate_cols = min_candidate_cols
        self.min_header_score = min_header_score
        self.text_ratio_weight = text_ratio_weight
        self.following_data_weight = following_data_weight
        self.max_column_jump_bonus = max_column_jump_bonus
        self.worksheet_as_chargrid = (
            worksheet_as_chargrid if worksheet_as_chargrid is not None else WorksheetAsChar(worksheet)
        )  # type: ignore

    def detect(self) -> list[TableRegion]:
        """Detect all table regions in the worksheet by analyzing character grid."""
        if len(self.worksheet_as_chargrid) == 0:
            return []

        occupied = set()
        for row_idx in range(len(self.worksheet_as_chargrid)):
            line = self.worksheet_as_chargrid[row_idx]
            for col_idx, char in enumerate(line):
                if char != " ":
                    occupied.add((row_idx, col_idx))

        if not occupied:
            return []

        max_cols = self.worksheet_as_chargrid.get_max_cols()
        components = self._find_connected_components(occupied, len(self.worksheet_as_chargrid), max_cols)
        tables = []

        header_detector = self._create_header_detector()

        for component in components:
            table = self._component_to_table(component)
            if table:
                adjusted_table = header_detector.adjust_table_start_row(table)
                if adjusted_table and self._is_valid_table(adjusted_table):
                    tables.append(adjusted_table)

        tables = self._filter_small_isolated_tables(tables)

        return tables

    def _create_header_detector(self) -> TableHeaderDetectorChar:
        """Create header detector with current configuration."""
        return TableHeaderDetectorChar(
            char_grid=self.worksheet_as_chargrid,
            header_candidate_limit=self.header_candidate_limit,
            min_candidate_cols=self.min_candidate_cols,
            min_header_score=self.min_header_score,
            text_ratio_weight=self.text_ratio_weight,
            following_data_weight=self.following_data_weight,
            max_column_jump_bonus=self.max_column_jump_bonus,
        )

    def _find_connected_components(
        self, occupied: set[tuple[int, int]], max_rows: int, max_cols: int
    ) -> list[set[tuple[int, int]]]:
        """Find connected components using row-span-based vertical connectivity.

        Groups cells into components by analyzing row spans. Two rows are considered connected
        if their column spans overlap (even partially). This handles tables with sparse rows
        that have large horizontal gaps within the same row.

        Algorithm:
        1. Group occupied cells by row number
        2. For each row, calculate column span (min to max column with data)
        3. Build connectivity graph where rows are connected if spans overlap
        4. Use flood-fill on the row connectivity graph to find components
        5. Return all cells from connected rows as a single component

        This approach handles sparse rows with gaps better than pure 8-directional flood-fill,
        which breaks connectivity when there are large horizontal gaps within a row.
        """
        row_cells = {}
        for row, col in occupied:
            if row not in row_cells:
                row_cells[row] = set()
            row_cells[row].add(col)

        row_spans = {}
        for row, cols in row_cells.items():
            min_col = min(cols)
            max_col = max(cols)
            row_spans[row] = (min_col, max_col)

        row_graph = {row: set() for row in row_spans}
        sorted_rows = sorted(row_spans.keys())
        max_row_gap = 1
        for i, row1 in enumerate(sorted_rows):
            min1, max1 = row_spans[row1]
            for row2 in sorted_rows[i + 1 :]:
                if row2 > row1 + max_row_gap:
                    break
                min2, max2 = row_spans[row2]
                if max1 >= min2 and max2 >= min1:
                    row_graph[row1].add(row2)
                    row_graph[row2].add(row1)

        visited_rows = set()
        components = []

        for start_row in row_spans:
            if start_row in visited_rows:
                continue

            component = set()
            row_stack = [start_row]

            while row_stack:
                row = row_stack.pop()
                if row in visited_rows:
                    continue

                visited_rows.add(row)
                for col in row_cells[row]:
                    component.add((row, col))

                for neighbor_row in row_graph[row]:
                    if neighbor_row not in visited_rows:
                        row_stack.append(neighbor_row)

            if component:
                components.append(component)

        return components

    def _component_to_table(self, component: set[tuple[int, int]]) -> TableRegion | None:
        """Convert connected component to table region.

        Finds the bounding rectangle by determining min/max row and column indices. Converts from
        0-indexed character grid positions to 1-indexed Excel cell positions (openpyxl convention).
        Returns TableRegion with 1-based coordinates.
        """
        if not component:
            return None

        rows = [pos[0] for pos in component]
        cols = [pos[1] for pos in component]

        start_row = min(rows)
        end_row = max(rows)
        start_col = min(cols)
        end_col = max(cols)

        return TableRegion(
            sheet_name=self.worksheet.title if self.worksheet else "Sheet",
            start_row=start_row + 1,
            end_row=end_row + 1,
            start_col=start_col + 1,
            end_col=end_col + 1,
            header_row=None,
            worksheet=self.worksheet,
        )

    def _filter_small_isolated_tables(self, tables: list[TableRegion]) -> list[TableRegion]:
        """Filter out small tables that are likely metadata or titles.

        If multiple tables are detected, removes small tables that are significantly smaller
        than the largest table and are separated by empty rows. This handles cases where
        sheet titles or metadata are detected as separate tables.

        Strategy:
        - If only one table, return as-is
        - Find the largest table by cell count
        - Remove tables that are less than 10% the size of the largest table
        """
        if len(tables) <= 1:
            return tables

        def table_size(t: TableRegion) -> int:
            return (t.end_row - t.start_row + 1) * (t.end_col - t.start_col + 1)

        largest_size = max(table_size(t) for t in tables)
        size_threshold = largest_size * 0.1

        filtered_tables = [t for t in tables if table_size(t) >= size_threshold]

        return filtered_tables if filtered_tables else tables

    def _is_valid_table(self, table: TableRegion) -> bool:
        """Validate table against minimum requirements using character grid.

        Checks table has at least min_rows rows, min_cols columns, and min_data_density ratio of
        non-space characters to total cells.
        """
        num_rows = table.end_row - table.start_row + 1
        num_cols = table.end_col - table.start_col + 1

        if num_rows < self.min_rows or num_cols < self.min_cols:
            return False

        total_cells = num_rows * num_cols
        if total_cells == 0:
            return False

        non_empty_cells = 0
        for row_idx in range(table.start_row - 1, table.end_row):
            if row_idx >= len(self.worksheet_as_chargrid):
                continue
            line = self.worksheet_as_chargrid[row_idx]
            for col_idx in range(table.start_col - 1, table.end_col):
                if col_idx < len(line) and line[col_idx] != " ":
                    non_empty_cells += 1

        density = non_empty_cells / total_cells

        return density >= self.min_data_density
