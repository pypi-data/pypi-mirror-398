from aixtools.agents.context.processors.table_detector.table_region import TableRegion


class CharGridDetectorCol:
    """Detects tables based on consecutive columns with non-empty cells.

    Algorithm:
    1. Parse character grid and transpose to work with columns
    2. For each column, identify occupied rows (non-space characters)
    3. Keep columns with at least min_rows occupied rows
    4. Calculate row span (min to max row) for each qualifying column
    5. Group consecutive columns together if gap between columns <= max_col_gap
    6. Create table region for each group with >= min_cols columns
    7. Table bounds are the union of all column spans in the group
    """

    def __init__(self, min_rows: int = 2, min_cols: int = 2, max_col_gap: int = 2):
        self.min_rows = min_rows
        self.min_cols = min_cols
        self.max_col_gap = max_col_gap

    def detect(self, char_grid: str, sheet_name: str) -> list[TableRegion]:
        """Detect tables based on column density in character grid."""
        lines = char_grid.split("\n")
        if not lines:
            return []

        max_width = max(len(line) for line in lines) if lines else 0
        if max_width == 0:
            return []

        col_spans = []
        for col_idx in range(max_width):
            occupied_rows = []
            for row_idx, line in enumerate(lines):
                if col_idx < len(line) and line[col_idx] != " ":
                    occupied_rows.append(row_idx)

            if len(occupied_rows) >= self.min_rows:
                min_row = min(occupied_rows)
                max_row = max(occupied_rows)
                col_spans.append((col_idx, min_row, max_row))

        if not col_spans:
            return []

        groups = []
        current_group = [col_spans[0]]

        for i in range(1, len(col_spans)):
            prev_col_idx = col_spans[i - 1][0]
            curr_col_idx = col_spans[i][0]

            if curr_col_idx - prev_col_idx <= self.max_col_gap + 1:
                current_group.append(col_spans[i])
            else:
                if len(current_group) >= self.min_cols:
                    groups.append(current_group)
                current_group = [col_spans[i]]

        if len(current_group) >= self.min_cols:
            groups.append(current_group)

        tables = []
        for group in groups:
            min_col = min(col_idx for col_idx, _, _ in group)
            max_col = max(col_idx for col_idx, _, _ in group)
            min_row = min(min_r for _, min_r, _ in group)
            max_row = max(max_r for _, _, max_r in group)

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
