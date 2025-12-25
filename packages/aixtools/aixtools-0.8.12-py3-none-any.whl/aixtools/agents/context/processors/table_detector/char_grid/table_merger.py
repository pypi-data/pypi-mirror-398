from aixtools.agents.context.processors.table_detector.table_region import TableRegion


class TableMerger:
    """Merges overlapping or adjacent table regions from multiple detectors.

    Algorithm:
    1. Collect all detected tables from different detectors
    2. Sort tables by area (largest first) for priority-based merging
    3. Iterate through tables and merge if they overlap or are adjacent
    4. Continue until no more merges are possible
    5. Return consolidated list of non-overlapping tables
    """

    def __init__(self, max_gap: int = 1):
        self.max_gap = max_gap

    def merge(self, table_lists: list[list[TableRegion]]) -> list[TableRegion]:
        """Merge tables from multiple detector outputs."""
        all_tables = []
        for tables in table_lists:
            all_tables.extend(tables)

        if not all_tables:
            return []

        all_tables.sort(key=lambda t: t.area(), reverse=True)

        merged = True
        while merged:
            merged = False
            new_tables = []
            used = set()

            for i, table_i in enumerate(all_tables):
                if i in used:
                    continue

                current = table_i
                for j, table_j in enumerate(all_tables[i + 1 :], start=i + 1):
                    if j in used:
                        continue

                    if current.overlaps(table_j) or current.is_adjacent(table_j, self.max_gap):
                        current = current.merge(table_j)
                        used.add(j)
                        merged = True

                new_tables.append(current)

            all_tables = new_tables

        return all_tables
