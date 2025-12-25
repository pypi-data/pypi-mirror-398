from aixtools.agents.context.processors.table_detector.table_region import TableRegion


class CharGridDetectorFlood:
    """Detects tables using flood-fill algorithm from non-empty cells.

    Algorithm:
    1. Parse character grid to identify all occupied cells (non-space)
    2. Find connected components using 8-directional flood-fill (including diagonals)
    3. For each connected component, extract bounding rectangle
    4. Create table region for each component with >= min_rows and >= min_cols
    """

    def __init__(self, min_rows: int = 2, min_cols: int = 2):
        self.min_rows = min_rows
        self.min_cols = min_cols

    def detect(self, char_grid: str, sheet_name: str) -> list[TableRegion]:
        """Detect tables using flood-fill on character grid."""
        lines = char_grid.split("\n")
        if not lines:
            return []

        occupied = set()
        for row_idx, line in enumerate(lines):
            for col_idx, char in enumerate(line):
                if char != " ":
                    occupied.add((row_idx, col_idx))

        if not occupied:
            return []

        visited = set()
        components = []

        for cell in occupied:
            if cell in visited:
                continue

            component = self._flood_fill(cell, occupied, visited)
            if component:
                components.append(component)

        tables = []
        for component in components:
            min_row = min(r for r, c in component)
            max_row = max(r for r, c in component)
            min_col = min(c for r, c in component)
            max_col = max(c for r, c in component)

            height = max_row - min_row + 1
            width = max_col - min_col + 1

            if height >= self.min_rows and width >= self.min_cols:
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

    def _flood_fill(
        self, start: tuple[int, int], occupied: set[tuple[int, int]], visited: set[tuple[int, int]]
    ) -> set[tuple[int, int]]:
        """Perform flood-fill from start cell using 8-directional connectivity."""
        stack = [start]
        component = set()

        while stack:
            cell = stack.pop()
            if cell in visited or cell not in occupied:
                continue

            visited.add(cell)
            component.add(cell)

            row, col = cell
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    neighbor = (row + dr, col + dc)
                    if neighbor in occupied and neighbor not in visited:
                        stack.append(neighbor)

        return component
