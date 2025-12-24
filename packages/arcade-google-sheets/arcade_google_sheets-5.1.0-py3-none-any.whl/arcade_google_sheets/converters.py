from arcade_google_sheets.enums import Dimension
from arcade_google_sheets.models import CellValue, SheetDataInput, ValueRange
from arcade_google_sheets.utils import (
    col_to_index,
    group_contiguous_rows,
    index_to_col,
)


class SheetDataInputToValueRangesConverter:
    def __init__(self, sheet_name: str, sheet_data: SheetDataInput):
        self.sheet_name = sheet_name
        self.sheet_data = sheet_data

    def convert(self) -> list[ValueRange]:
        """
        Convert a SheetDataInput to a list of ValueRanges that are row-oriented.

        Args:
            sheet_name (str): The name of the sheet to which the data belongs.
            sheet_data (SheetDataInput): The data to convert into ranges.

        Returns:
            list[ValueRange]: The converted ValueRanges.
        """
        if not self.sheet_data.data:
            return []

        row_ranges = self._build_row_oriented_ranges()

        return row_ranges

    def _to_float_if_int(self, value: CellValue) -> bool | str | float:
        """
        The spreadsheets.values.batchUpdate API does not support int values.
        So we convert ints to floats.

        Args:
            value (Any): The value to possibly convert.

        Returns:
            bool | str | float: The converted value.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return float(value)
        return value

    def _get_cell_value(self, row_num: int, col_idx: int) -> bool | str | float:
        """
        Safely fetch a cell value.

        Args:
            row_num (int): The row number of the cell.
            col_idx (int): The column index of the cell.

        Returns:
            bool | str | float: The value of the cell.
        """
        col_letter = index_to_col(col_idx)
        return self._to_float_if_int(self.sheet_data.data[row_num][col_letter])

    def _build_row_oriented_ranges(self) -> list[ValueRange]:
        """
        Build row-oriented ValueRanges for the object's sheet data.

        Returns:
            list[ValueRange]: The row-oriented ValueRanges.
        """
        # Map (start_col_idx, end_col_idx) -> { row_num: [values across columns] }
        segment_to_rows_values: dict[tuple[int, int], dict[int, list[bool | str | float]]] = {}

        for row_num in sorted(self.sheet_data.data):
            cols_dict = self.sheet_data.data[row_num]
            col_indices = sorted(col_to_index(col) for col in cols_dict)
            if not col_indices:
                continue
            contiguous_groups = group_contiguous_rows(col_indices)
            for group in contiguous_groups:
                start_idx = group[0]
                end_idx = group[-1]
                row_values = [self._get_cell_value(row_num, ci) for ci in group]
                key = (start_idx, end_idx)
                if key not in segment_to_rows_values:
                    segment_to_rows_values[key] = {}
                segment_to_rows_values[key][row_num] = row_values

        row_oriented_ranges: list[ValueRange] = []
        for (start_idx, end_idx), rows_map in segment_to_rows_values.items():
            sorted_rows = sorted(rows_map.keys())
            row_groups = group_contiguous_rows(sorted_rows)
            for rg in row_groups:
                start_row = rg[0]
                end_row = rg[-1]
                start_col = index_to_col(start_idx)
                end_col = index_to_col(end_idx)
                a1_range = f"'{self.sheet_name}'!{start_col}{start_row}:{end_col}{end_row}"
                values = [rows_map[r] for r in rg]
                row_oriented_ranges.append(
                    ValueRange(
                        range=a1_range,
                        majorDimension=Dimension.ROWS,
                        values=values,
                    )
                )

        return row_oriented_ranges
