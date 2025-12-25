"""Table detector based on character grid representation."""

from aixtools.agents.context.processors.table_detector.char_grid.table_detector_sheet_char import (
    TableDetectorSheetCharGrid,
)
from aixtools.agents.context.processors.table_detector.table_detector_base import TableDetectorBase
from aixtools.agents.context.processors.table_detector.table_region import TableRegion


class TableDetectorCharGrid(TableDetectorBase):
    """Detect tables by finding rectangular blocks in character grid representation.

    Delegates sheet-level detection to TableDetectorSheetChar.
    """

    def _detect_tables(self, sheet) -> list[TableRegion]:
        """Detect all table regions in a worksheet by analyzing character grid."""
        detector = TableDetectorSheetCharGrid(
            worksheet=sheet,
            min_rows=self.min_rows,
            min_cols=self.min_cols,
            min_data_density=self.min_data_density,
            header_candidate_limit=self.header_candidate_limit,
            min_candidate_cols=self.min_candidate_cols,
            min_header_score=self.min_header_score,
            text_ratio_weight=self.text_ratio_weight,
            following_data_weight=self.following_data_weight,
            max_column_jump_bonus=self.max_column_jump_bonus,
        )
        return detector.detect()
