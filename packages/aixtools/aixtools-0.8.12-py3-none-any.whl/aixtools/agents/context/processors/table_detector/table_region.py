import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from openpyxl.worksheet.worksheet import Worksheet


@dataclass
class TableRegion:
    """Represents a detected table region in a worksheet.

    All coordinates (start_row, end_row, start_col, end_col, header_row) use 1-based indexing
    to match Excel's coordinate system and openpyxl's cell() method. Row 1 is the first row,
    Column 1 is the first column (A).

    The coordinates represent an inclusive range: both start and end positions are included
    in the table region.
    """

    sheet_name: str
    start_row: int  # 1-based, inclusive
    start_col: int  # 1-based, inclusive
    end_row: int  # 1-based, inclusive
    end_col: int  # 1-based, inclusive
    header_row: int | None  # 1-based if present
    worksheet: Worksheet | None = None

    def __str__(self) -> str:
        row_count = self.end_row - self.start_row + 1
        return (
            f"Table({self.sheet_name}[{self.start_row}:{self.end_row}, "
            f"{self.start_col}:{self.end_col}], header={self.header_row}, rows={row_count})"
        )

    def area(self) -> int:
        """Calculate area of the table region."""
        return (self.end_row - self.start_row + 1) * (self.end_col - self.start_col + 1)

    def height(self) -> int:
        """Calculate height (number of rows)."""
        return self.end_row - self.start_row + 1

    def is_adjacent(self, other: "TableRegion", max_gap: int = 1) -> bool:
        """Check if this table is adjacent to another within max_gap."""
        vertical_gap = min(abs(self.end_row - other.start_row), abs(other.end_row - self.start_row))
        horizontal_gap = min(abs(self.end_col - other.start_col), abs(other.end_col - self.start_col))

        rows_overlap = not (self.end_row + max_gap < other.start_row or self.start_row > other.end_row + max_gap)
        cols_overlap = not (self.end_col + max_gap < other.start_col or self.start_col > other.end_col + max_gap)

        return (rows_overlap and horizontal_gap <= max_gap) or (cols_overlap and vertical_gap <= max_gap)

    def merge(self, other: "TableRegion") -> "TableRegion":
        """Merge this table with another, returning a new table."""
        return TableRegion(
            sheet_name=self.sheet_name,
            start_row=min(self.start_row, other.start_row),
            end_row=max(self.end_row, other.end_row),
            start_col=min(self.start_col, other.start_col),
            end_col=max(self.end_col, other.end_col),
            header_row=None,
            worksheet=self.worksheet,
        )

    def overlaps(self, other: "TableRegion") -> bool:
        """Check if this table overlaps with another."""
        return not (
            self.end_row < other.start_row
            or self.start_row > other.end_row
            or self.end_col < other.start_col
            or self.start_col > other.end_col
        )

    def width(self) -> int:
        """Calculate width (number of columns)."""
        return self.end_col - self.start_col + 1

    @classmethod
    def load(cls, json_path: Path, worksheet: Worksheet | None = None) -> "TableRegion":
        """Load table metadata from JSON file and attach worksheet reference."""
        with open(json_path) as f:
            data = json.load(f)
        return cls(
            sheet_name=data["sheet_name"],
            start_row=data["start_row"],
            end_row=data["end_row"],
            start_col=data["start_col"],
            end_col=data["end_col"],
            header_row=data["header_row"],
            worksheet=worksheet,
        )

    def save(self, base_path: Path):
        """Save table as CSV and JSON metadata."""
        df = self.to_dataframe()
        if not df.empty:
            csv_path = base_path.with_suffix(".csv")
            json_path = base_path.with_suffix(".json")

            df.to_csv(csv_path, index=False)

            with open(json_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert table region to pandas DataFrame by reading from worksheet.

        If header_row is set, uses that row as the header. Otherwise, defaults to
        using the first row (start_row) as the header.
        """
        if self.worksheet is None:
            return pd.DataFrame()

        data = []
        for row_idx in range(self.start_row, self.end_row + 1):
            row_data = []
            for col_idx in range(self.start_col, self.end_col + 1):
                cell = self.worksheet.cell(row_idx, col_idx)
                row_data.append(cell.value)
            data.append(tuple(row_data))

        if not data:
            return pd.DataFrame()

        header_offset = (self.header_row - self.start_row) if self.header_row is not None else 0

        if 0 <= header_offset < len(data):
            headers = [str(h) if h is not None else f"Column_{i}" for i, h in enumerate(data[header_offset])]
            headers = self._make_unique_headers(headers)
            data_rows = data[header_offset + 1 :]
            df = pd.DataFrame(data_rows, columns=headers)
            return self._convert_columns_to_consistent_types(df)

        df = pd.DataFrame(data)
        return self._convert_columns_to_consistent_types(df)

    def to_dict(self) -> dict:
        """Convert TableRegion to dictionary, excluding worksheet reference."""
        row_count = self.end_row - self.start_row + 1
        col_count = self.end_col - self.start_col + 1
        return {
            "sheet_name": self.sheet_name,
            "start_row": self.start_row,
            "end_row": self.end_row,
            "start_col": self.start_col,
            "end_col": self.end_col,
            "header_row": self.header_row,
            "row_count": row_count,
            "col_count": col_count,
        }

    def _convert_columns_to_consistent_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns with mixed types to consistent types for Arrow compatibility."""
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].apply(
                    lambda x: str(x) if x is not None and not (isinstance(x, float) and pd.isna(x)) else None
                )
        return df

    def _make_unique_headers(self, headers: list[str]) -> list[str]:
        """Make column headers unique by appending suffix to duplicates."""
        seen = {}
        unique_headers = []
        for header in headers:
            if header not in seen:
                seen[header] = 0
                unique_headers.append(header)
            else:
                seen[header] += 1
                unique_headers.append(f"{header}_{seen[header]}")
        return unique_headers
