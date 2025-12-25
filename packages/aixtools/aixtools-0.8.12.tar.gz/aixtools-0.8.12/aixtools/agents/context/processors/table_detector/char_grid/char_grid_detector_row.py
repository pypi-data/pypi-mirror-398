from aixtools.agents.context.processors.table_detector.table_region import TableRegion


class CharGridDetectorRow:
    """Detects tables based on consecutive rows with non-empty cells.

    Algorithm:
    1. Parse character grid line by line
    2. For each row, identify occupied columns (non-space characters)
    3. Keep rows with at least min_cols occupied columns
    4. Calculate column span (min to max column) for each qualifying row
    5. Group consecutive rows together if gap between rows <= max_row_gap
    6. Create table region for each group with >= min_rows rows
    7. Table bounds are the union of all row spans in the group
    """

    def __init__(self, min_rows: int = 2, min_cols: int = 2, max_row_gap: int = 2):
        self.min_rows = min_rows
        self.min_cols = min_cols
        self.max_row_gap = max_row_gap

    def detect(self, char_grid: str, sheet_name: str) -> list[TableRegion]:
        """Detect tables based on row density in character grid."""
        lines = char_grid.split("\n")
        if not lines:
            return []

        row_spans = []
        for row_idx, line in enumerate(lines):
            occupied_cols = [col_idx for col_idx, char in enumerate(line) if char != " "]
            if len(occupied_cols) >= self.min_cols:
                min_col = min(occupied_cols)
                max_col = max(occupied_cols)
                row_spans.append((row_idx, min_col, max_col))

        if not row_spans:
            return []

        groups = []
        current_group = [row_spans[0]]

        for i in range(1, len(row_spans)):
            prev_row_idx = row_spans[i - 1][0]
            curr_row_idx = row_spans[i][0]

            if curr_row_idx - prev_row_idx <= self.max_row_gap + 1:
                current_group.append(row_spans[i])
            else:
                if len(current_group) >= self.min_rows:
                    groups.append(current_group)
                current_group = [row_spans[i]]

        if len(current_group) >= self.min_rows:
            groups.append(current_group)

        tables = []
        for group in groups:
            min_row = min(row_idx for row_idx, _, _ in group)
            max_row = max(row_idx for row_idx, _, _ in group)
            min_col = min(min_c for _, min_c, _ in group)
            max_col = max(max_c for _, _, max_c in group)

            table = TableRegion(
                sheet_name=sheet_name,
                start_row=min_row + 1,
                end_row=max_row + 1,
                start_col=min_col + 1,
                end_col=max_col + 1,
                header_row=None,
                worksheet=None,
            )
            tables.append(table)

        return tables
