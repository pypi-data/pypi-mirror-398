import logging
import string
from typing import Any

from arcade_mcp_server.exceptions import RetryableToolError, ToolExecutionError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from arcade_google_sheets.constants import (
    DEFAULT_SHEET_COLUMN_COUNT,
    DEFAULT_SHEET_ROW_COUNT,
)
from arcade_google_sheets.enums import (
    Corpora,
    NumberFormatType,
    OrderBy,
    SheetIdentifierType,
)
from arcade_google_sheets.models import (
    CellData,
    CellExtendedValue,
    CellFormat,
    GridData,
    GridProperties,
    NumberFormat,
    RowData,
    Sheet,
    SheetDataInput,
    SheetProperties,
    Spreadsheet,
    ValueRange,
)
from arcade_google_sheets.templates import sheet_url_template
from arcade_google_sheets.types import CellValue

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def remove_none_values(params: dict) -> dict:
    """
    Remove None values from a dictionary.
    :param params: The dictionary to clean
    :return: A new dictionary with None values removed
    """
    return {k: v for k, v in params.items() if v is not None}


def build_sheets_service(auth_token: str | None) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Sheets service object.
    """
    auth_token = auth_token or ""
    return build("sheets", "v4", credentials=Credentials(auth_token))


def build_drive_service(auth_token: str | None) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Drive service object.
    """
    auth_token = auth_token or ""
    return build("drive", "v3", credentials=Credentials(auth_token))


def col_to_index(col: str) -> int:
    """Convert a sheet's column string to a 0-indexed column index

    Args:
        col (str): The column string to convert. e.g., "A", "AZ", "QED"

    Returns:
        int: The 0-indexed column index.
    """
    result = 0
    for char in col.upper():
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result - 1


def index_to_col(index: int) -> str:
    """Convert a 0-indexed column index to its corresponding column string

    Args:
        index (int): The 0-indexed column index to convert.

    Returns:
        str: The column string. e.g., "A", "AZ", "QED"
    """
    result = ""
    index += 1
    while index > 0:
        index, rem = divmod(index - 1, 26)
        result = chr(rem + ord("A")) + result
    return result


def is_col_greater(col1: str, col2: str) -> bool:
    """Determine if col1 represents a column that comes after col2 in a sheet

    This comparison is based on:
      1. The length of the column string (longer means greater).
      2. Lexicographical comparison if both strings are the same length.

    Args:
        col1 (str): The first column string to compare.
        col2 (str): The second column string to compare.

    Returns:
        bool: True if col1 comes after col2, False otherwise.
    """
    if len(col1) != len(col2):
        return len(col1) > len(col2)
    return col1.upper() > col2.upper()


def compute_sheet_data_dimensions(
    sheet_data_input: SheetDataInput,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Compute the dimensions of a sheet based on the data provided.

    Args:
        sheet_data_input (SheetDataInput):
            The data to compute the dimensions of.

    Returns:
        tuple[tuple[int, int], tuple[int, int]]: The dimensions of the sheet. The first tuple
            contains the row range (start, end) and the second tuple contains the column range
            (start, end).
    """
    max_row = 0
    min_row = 10_000_000  # max number of cells in a sheet
    max_col_str = None
    min_col_str = None

    for key, row in sheet_data_input.data.items():
        try:
            row_num = int(key)
        except ValueError:
            continue
        if row_num > max_row:
            max_row = row_num
        if row_num < min_row:
            min_row = row_num

        if isinstance(row, dict):
            for col in row:
                # Update max column string
                if max_col_str is None or is_col_greater(col, max_col_str):
                    max_col_str = col
                # Update min column string
                if min_col_str is None or is_col_greater(min_col_str, col):
                    min_col_str = col

    max_col_index = col_to_index(max_col_str) if max_col_str is not None else -1
    min_col_index = col_to_index(min_col_str) if min_col_str is not None else 0

    return (min_row, max_row), (min_col_index, max_col_index)


def create_sheet(sheet_data_input: SheetDataInput) -> Sheet:
    """Create a Google Sheet from a dictionary of data.

    Args:
        sheet_data_input (SheetDataInput): The data to create the sheet from.

    Returns:
        Sheet: The created sheet.
    """
    (_, max_row), (min_col_index, max_col_index) = compute_sheet_data_dimensions(sheet_data_input)
    sheet_data = create_sheet_data(sheet_data_input, min_col_index, max_col_index)
    sheet_properties = create_sheet_properties(
        row_count=max(DEFAULT_SHEET_ROW_COUNT, max_row),
        column_count=max(DEFAULT_SHEET_COLUMN_COUNT, max_col_index + 1),
    )

    return Sheet(properties=sheet_properties, data=sheet_data)


def create_sheet_properties(
    sheet_id: int = 1,
    title: str = "Sheet1",
    row_count: int = DEFAULT_SHEET_ROW_COUNT,
    column_count: int = DEFAULT_SHEET_COLUMN_COUNT,
) -> SheetProperties:
    """Create a SheetProperties object

    Args:
        sheet_id (int): The ID of the sheet.
        title (str): The title of the sheet.
        row_count (int): The number of rows in the sheet.
        column_count (int): The number of columns in the sheet.

    Returns:
        SheetProperties: The created sheet properties object.
    """
    return SheetProperties(
        sheetId=sheet_id,
        title=title,
        gridProperties=GridProperties(rowCount=row_count, columnCount=column_count),
    )


def group_contiguous_rows(row_numbers: list[int]) -> list[list[int]]:
    """Groups a sorted list of row numbers into contiguous groups

    A contiguous group is a list of row numbers that are consecutive integers.
    For example, [1,2,3,5,6] is converted to [[1,2,3],[5,6]].

    Args:
        row_numbers (list[int]): The list of row numbers to group.

    Returns:
        list[list[int]]: The grouped row numbers.
    """
    if not row_numbers:
        return []
    groups = []
    current_group = [row_numbers[0]]
    for r in row_numbers[1:]:
        if r == current_group[-1] + 1:
            current_group.append(r)
        else:
            groups.append(current_group)
            current_group = [r]
    groups.append(current_group)
    return groups


def create_cell_data(cell_value: CellValue) -> CellData:
    """
    Create a CellData object based on the type of cell_value.
    """
    if isinstance(cell_value, bool):
        return _create_bool_cell(cell_value)
    elif isinstance(cell_value, int):
        return _create_int_cell(cell_value)
    elif isinstance(cell_value, float):
        return _create_float_cell(cell_value)
    elif isinstance(cell_value, str):
        return _create_string_cell(cell_value)


def _create_formula_cell(cell_value: str) -> CellData:
    cell_val = CellExtendedValue(formulaValue=cell_value)
    return CellData(userEnteredValue=cell_val)


def _create_currency_cell(cell_value: str) -> CellData:
    value_without_symbol = cell_value[1:]
    try:
        num_value = int(value_without_symbol)
        cell_format = CellFormat(
            numberFormat=NumberFormat(type=NumberFormatType.CURRENCY, pattern="$#,##0")
        )
        cell_val = CellExtendedValue(numberValue=num_value)
        return CellData(userEnteredValue=cell_val, userEnteredFormat=cell_format)
    except ValueError:
        try:
            num_value = float(value_without_symbol)  # type: ignore[assignment]
            cell_format = CellFormat(
                numberFormat=NumberFormat(type=NumberFormatType.CURRENCY, pattern="$#,##0.00")
            )
            cell_val = CellExtendedValue(numberValue=num_value)
            return CellData(userEnteredValue=cell_val, userEnteredFormat=cell_format)
        except ValueError:
            return CellData(userEnteredValue=CellExtendedValue(stringValue=cell_value))


def _create_percent_cell(cell_value: str) -> CellData:
    try:
        num_value = float(cell_value[:-1].strip())
        cell_format = CellFormat(
            numberFormat=NumberFormat(type=NumberFormatType.PERCENT, pattern="0.00%")
        )
        cell_val = CellExtendedValue(numberValue=num_value)
        return CellData(userEnteredValue=cell_val, userEnteredFormat=cell_format)
    except ValueError:
        return CellData(userEnteredValue=CellExtendedValue(stringValue=cell_value))


def _create_bool_cell(cell_value: bool) -> CellData:
    return CellData(userEnteredValue=CellExtendedValue(boolValue=cell_value))


def _create_int_cell(cell_value: int) -> CellData:
    cell_format = CellFormat(
        numberFormat=NumberFormat(type=NumberFormatType.NUMBER, pattern="#,##0")
    )
    return CellData(
        userEnteredValue=CellExtendedValue(numberValue=cell_value), userEnteredFormat=cell_format
    )


def _create_float_cell(cell_value: float) -> CellData:
    cell_format = CellFormat(
        numberFormat=NumberFormat(type=NumberFormatType.NUMBER, pattern="#,##0.00")
    )
    return CellData(
        userEnteredValue=CellExtendedValue(numberValue=cell_value), userEnteredFormat=cell_format
    )


def _create_string_cell(cell_value: str) -> CellData:
    if cell_value.startswith("="):
        return _create_formula_cell(cell_value)
    elif cell_value.startswith("$") and len(cell_value) > 1:
        return _create_currency_cell(cell_value)
    elif cell_value.endswith("%") and len(cell_value) > 1:
        return _create_percent_cell(cell_value)

    return CellData(userEnteredValue=CellExtendedValue(stringValue=cell_value))


def create_row_data(
    row_data: dict[str, CellValue], min_col_index: int, max_col_index: int
) -> RowData:
    """Constructs RowData for a single row using the provided row_data.

    Args:
        row_data (dict[str, CellValue]): The data to create the row from.
        min_col_index (int): The minimum column index from the SheetDataInput.
        max_col_index (int): The maximum column index from the SheetDataInput.
    """
    row_cells = []
    for col_idx in range(min_col_index, max_col_index + 1):
        col_letter = index_to_col(col_idx)
        if col_letter in row_data:
            cell_data = create_cell_data(row_data[col_letter])
        else:
            cell_data = CellData(userEnteredValue=CellExtendedValue(stringValue=""))
        row_cells.append(cell_data)
    return RowData(values=row_cells)


def create_sheet_data(
    sheet_data_input: SheetDataInput,
    min_col_index: int,
    max_col_index: int,
) -> list[GridData]:
    """Create grid data from SheetDataInput by grouping contiguous rows and processing cells.

    Args:
        sheet_data_input (SheetDataInput): The data to create the sheet from.
        min_col_index (int): The minimum column index from the SheetDataInput.
        max_col_index (int): The maximum column index from the SheetDataInput.

    Returns:
        list[GridData]: The created grid data.
    """
    row_numbers = list(sheet_data_input.data.keys())
    if not row_numbers:
        return []

    sorted_rows = sorted(row_numbers)
    groups = group_contiguous_rows(sorted_rows)

    sheet_data = []
    for group in groups:
        rows_data = []
        for r in group:
            current_row_data = sheet_data_input.data.get(r, {})
            row = create_row_data(current_row_data, min_col_index, max_col_index)
            rows_data.append(row)
        grid_data = GridData(
            startRow=group[0] - 1,  # convert to 0-indexed
            startColumn=min_col_index,
            rowData=rows_data,
        )
        sheet_data.append(grid_data)

    return sheet_data


def parse_get_spreadsheet_response(api_response: dict) -> dict:
    """
    Parse the get spreadsheet Google Sheets API response into a structured dictionary.
    """
    properties = api_response.get("properties") or {}
    sheets = [parse_sheet(sheet) for sheet in (api_response.get("sheets") or [])]

    return {
        "title": properties.get("title", ""),
        "spreadsheetId": api_response.get("spreadsheetId", ""),
        "spreadsheetUrl": api_response.get("spreadsheetUrl", ""),
        "sheets": sheets,
    }


def parse_sheet(api_sheet: dict) -> dict:
    """
    Parse an individual sheet's data from the Google Sheets 'get spreadsheet'
    API response into a structured dictionary.
    """
    props = api_sheet.get("properties") or {}
    grid_props = props.get("gridProperties") or {}
    cell_data = convert_api_grid_data_to_dict(api_sheet.get("data") or [])

    return {
        "sheetId": props.get("sheetId"),
        "title": props.get("title", ""),
        "rowCount": grid_props.get("rowCount", 0),
        "columnCount": grid_props.get("columnCount", 0),
        "data": cell_data,
    }


def extract_user_entered_cell_value(cell: dict) -> Any:
    """
    Extract the user entered value from a cell's 'userEnteredValue'.

    Args:
        cell (dict): A cell dictionary from the grid data.

    Returns:
        The extracted value if present, otherwise None.
    """
    if not isinstance(cell, dict):
        return ""
    user_val = cell.get("userEnteredValue") or {}
    for key in ["stringValue", "numberValue", "boolValue", "formulaValue"]:
        if key in user_val:
            return user_val[key]

    return ""


def process_row(row: dict, start_column_index: int) -> dict:
    """
    Process a single row from grid data, converting non-empty cells into a dictionary
    that maps column letters to cell values.

    Args:
        row (dict): A row from the grid data.
        start_column_index (int): The starting column index for this row.

    Returns:
        dict: A mapping of column letters to cell values for non-empty cells.
    """
    row_result = {}
    for j, cell in enumerate(row.get("values") or []):
        cell_dict = cell if isinstance(cell, dict) else {}
        column_index = start_column_index + j
        column_string = index_to_col(column_index)
        user_entered_cell_value = extract_user_entered_cell_value(cell_dict)
        formatted_cell_value = cell_dict.get("formattedValue", "")

        if user_entered_cell_value != "" or formatted_cell_value != "":
            row_result[column_string] = {
                "userEnteredValue": user_entered_cell_value,
                "formattedValue": formatted_cell_value,
            }

    return row_result


def convert_api_grid_data_to_dict(grids: list[dict]) -> dict:
    """
    Convert a list of grid data dictionaries from the 'get spreadsheet' API
    response into a structured cell dictionary.

    The returned dictionary maps row numbers to sub-dictionaries that map column letters
    (e.g., 'A', 'B', etc.) to their corresponding non-empty cell values.

    Args:
        grids (list[dict]): The list of grid data dictionaries from the API.

    Returns:
        dict: A dictionary mapping row numbers to dictionaries of column letter/value pairs.
            Only includes non-empty rows and non-empty cells.
    """
    if not grids:
        return {}
    result = {}
    for grid in grids:
        if not isinstance(grid, dict):
            continue
        start_row = grid.get("startRow", 0)
        start_column = grid.get("startColumn", 0)

        for i, row in enumerate(grid.get("rowData") or [], start=1):
            current_row = start_row + i
            row_dict = row if isinstance(row, dict) else {}
            row_data = process_row(row_dict, start_column)

            if row_data:
                result[current_row] = row_data

    return dict(sorted(result.items()))


def validate_sheet_data_input(data: str | None) -> SheetDataInput:
    """
    Validate and convert data to SheetDataInput, raising RetryableToolError on validation failure.
    `data` is a JSON string representing a dictionary that maps row numbers to dictionaries that map
    column letters to cell values.

    Args:
        data: The data parameter to validate, a JSON string representing a dictionary that maps
        row numbers to dictionaries that map column letters to cell values.
        Type hint: dict[int, dict[str, int | float | str | bool]]

    Returns:
        SheetDataInput: The validated sheet data input object

    Raises:
        RetryableToolError: If the data is invalid JSON or has an unexpected format
    """
    try:
        return SheetDataInput(data=data)  # type: ignore[arg-type]
    except Exception as e:
        msg = "Invalid JSON or unexpected data format for parameter `data`"
        raise RetryableToolError(
            message=msg,
            additional_prompt_content=f"{msg}: {e}",
            retry_after_ms=100,
        )


def validate_write_to_cell_params(  # type: ignore[no-any-unimported]
    service: Resource,
    spreadsheet_id: str,
    sheet_name: str,
    column: str,
    row: int,
) -> None:
    """Validates the input parameters for the write to cell tool.

    Args:
        service (Resource): The Google Sheets service.
        spreadsheet_id (str): The ID of the spreadsheet provided to the tool.
        sheet_name (str): The name of the sheet provided to the tool.
        column (str): The column to write to provided to the tool.
        row (int): The row to write to provided to the tool.

    Raises:
        RetryableToolError:
            If the sheet name is not found in the spreadsheet
        ToolExecutionError:
            If the column is not alphabetical
            If the row is not a positive number
            If the row is out of bounds for the sheet
            If the column is out of bounds for the sheet
    """
    if not column.isalpha():
        raise ToolExecutionError(
            message=(
                f"Invalid column name {column}. "
                "It must be a non-empty string containing only letters"
            ),
        )

    if row < 1:
        raise ToolExecutionError(
            message=(f"Invalid row number {row}. It must be a positive integer greater than 0."),
        )

    sheet_properties = (
        service.spreadsheets()
        .get(
            spreadsheetId=spreadsheet_id,
            includeGridData=True,
            fields="sheets/properties/title,sheets/properties/gridProperties/rowCount,sheets/properties/gridProperties/columnCount",
        )
        .execute()
    )
    sheet_names = [sheet["properties"]["title"] for sheet in sheet_properties["sheets"]]
    sheet_row_count = sheet_properties["sheets"][0]["properties"]["gridProperties"]["rowCount"]
    sheet_column_count = sheet_properties["sheets"][0]["properties"]["gridProperties"][
        "columnCount"
    ]

    if sheet_name not in sheet_names:
        raise RetryableToolError(
            message=f"Sheet name {sheet_name} not found in spreadsheet with id {spreadsheet_id}",
            additional_prompt_content=f"Sheet names in the spreadsheet: {sheet_names}",
            retry_after_ms=100,
        )

    if row > sheet_row_count:
        raise ToolExecutionError(
            message=(
                f"Row {row} is out of bounds for sheet {sheet_name} "
                f"in spreadsheet with id {spreadsheet_id}. "
                f"Sheet only has {sheet_row_count} rows which is less than the requested row {row}"
            )
        )

    if col_to_index(column) > sheet_column_count:
        raise ToolExecutionError(
            message=(
                f"Column {column} is out of bounds for sheet {sheet_name} "
                f"in spreadsheet with id {spreadsheet_id}. "
                f"Sheet only has {sheet_column_count} columns which "
                f"is less than the requested column {column}"
            )
        )


def parse_write_to_cell_response(response: dict) -> dict:
    return {
        "spreadsheetId": response["spreadsheetId"],
        "sheetTitle": response["updatedData"]["range"].split("!")[0],
        "updatedCell": response["updatedData"]["range"].split("!")[1],
        "value": response["updatedData"]["values"][0][0],
    }


def calculate_a1_sheet_range(
    sheet_name: str,
    sheet_row_count: int,
    sheet_col_count: int,
    start_row: int,
    start_col: str,
    max_rows: int,
    max_cols: int,
) -> str | None:
    """Calculate a single range for a sheet based on start position and limits.

    Args:
        sheet_name (str): The name of the sheet.
        sheet_row_count (int): The number of rows in the sheet.
        sheet_col_count (int): The number of columns in the sheet.
        start_row (int): The row from which to start fetching data.
        start_col (str): The column letter(s) from which to start fetching data.
        max_rows (int): The maximum number of rows to fetch.
        max_cols (int): The maximum number of columns to fetch.

    Returns:
        str | None: The A1 range for the sheet, or None if there is no data to fetch.
    """
    start_col_index = col_to_index(start_col)

    effective_max_rows = min(sheet_row_count, max_rows or sheet_row_count)
    effective_max_cols = min(sheet_col_count, max_cols or sheet_col_count)

    end_row = min(start_row + effective_max_rows - 1, sheet_row_count)
    end_col_index = min(start_col_index + effective_max_cols - 1, sheet_col_count - 1)

    # Only create a range if there's actually data to fetch
    if start_row <= end_row and start_col_index <= end_col_index:
        range_start = f"{index_to_col(start_col_index)}{start_row}"
        range_end = f"{index_to_col(end_col_index)}{end_row}"
        return f"'{sheet_name}'!{range_start}:{range_end}"

    return None


def get_sheet_by_identifier(
    sheets: list[Sheet], sheet_identifier: str, sheet_identifier_type: SheetIdentifierType
) -> Sheet | None:
    """
    Find a sheet by identifier (name, sheet ID, or 1-based position index).

    Args:
        sheets (list): List of Sheet objects from the spreadsheet.
        sheet_identifier (str): The identifier of the sheet to get.
        sheet_identifier_type (SheetIdentifierType): The type of the identifier.

    Returns:
        Sheet | None: The matching sheet, or None if not found.
    """
    if sheet_identifier_type == SheetIdentifierType.POSITION:
        index = int(sheet_identifier) - 1
        if 0 <= index < len(sheets):
            return sheets[index]

    if sheet_identifier_type == SheetIdentifierType.ID_OR_NAME:
        for sheet in sheets:
            sheet_title = sheet.properties.title
            sheet_id = sheet.properties.sheetId
            if (
                sheet_title.casefold() == sheet_identifier.casefold()
                or str(sheet_id).casefold() == sheet_identifier.casefold()
            ):
                return sheet

    return None


def get_spreadsheet_metadata_helper(sheets_service: Resource, spreadsheet_id: str) -> Spreadsheet:  # type: ignore[no-any-unimported]
    """Get the spreadsheet metadata to collect the sheet names and dimensions

    Args:
        sheets_service (Resource): The Google Sheets service.
        spreadsheet_id (str): The ID of the spreadsheet provided to the tool.

    Returns:
        Spreadsheet: The spreadsheet with only the metadata.
    """
    metadata_response = (
        sheets_service.spreadsheets()
        .get(
            spreadsheetId=spreadsheet_id,
            includeGridData=False,
            fields="spreadsheetId,spreadsheetUrl,properties/title,sheets/properties",
        )
        .execute()
    )
    return Spreadsheet.model_validate(metadata_response)


def batch_update(service: Resource, spreadsheet_id: str, data: list[ValueRange]) -> dict:  # type: ignore[no-any-unimported]
    """
    Batch update a spreadsheet with a list of ValueRanges.

    Args:
        service (Resource): The Google Sheets service.
        spreadsheet_id (str): The ID of the spreadsheet to update.
        data (list[ValueRange]): The data to update the spreadsheet with.

    Returns:
        dict: The response from the batch update.
    """
    body = {
        "valueInputOption": "USER_ENTERED",
        "data": [value_range.model_dump() for value_range in data],
    }
    response = (
        service.spreadsheets()
        .values()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )
    updated_ranges = [
        value_response["updatedRange"] for value_response in (response.get("responses") or [])
    ]
    return {
        "spreadsheet_id": response["spreadsheetId"],
        "total_updated_rows": response["totalUpdatedRows"],
        "total_updated_columns": response["totalUpdatedColumns"],
        "total_updated_cells": response["totalUpdatedCells"],
        "updated_ranges": updated_ranges,
    }


def get_spreadsheet_with_pagination(  # type: ignore[no-any-unimported]
    service: Resource,
    spreadsheet_id: str,
    sheet_identifier: str,
    sheet_identifier_type: SheetIdentifierType,
    start_row: int,
    start_col: str,
    max_rows: int,
    max_cols: int,
) -> dict:
    """
    Get spreadsheet data with pagination support for large spreadsheets.

    Args:
        service (Resource): The Google Sheets service.
        spreadsheet_id (str): The ID of the spreadsheet provided to the tool.
        sheet_position (int | None): The position/tab of the sheet to get.
        sheet_id_or_name (str | None): The id or name of the sheet to get.
        start_row (int): The row from which to start fetching data.
        start_col (str): The column letter(s) from which to start fetching data.
        max_rows (int): The maximum number of rows to fetch.
        max_cols (int): The maximum number of columns to fetch.

    Returns:
        dict: The spreadsheet data for the specified sheet in the spreadsheet.

    """

    # First, only get the spreadsheet metadata to collect the sheet names and dimensions
    spreadsheet_with_only_metadata = get_spreadsheet_metadata_helper(service, spreadsheet_id)

    target_sheet = get_sheet_by_identifier(
        spreadsheet_with_only_metadata.sheets, sheet_identifier, sheet_identifier_type
    )
    if not target_sheet:
        raise ToolExecutionError(
            message=f"Sheet with identifier '{sheet_identifier}' not found",
            developer_message=(
                "Sheet(s) in the spreadsheet: "
                + ", ".join([
                    sheet.model_dump_json() for sheet in spreadsheet_with_only_metadata.sheets
                ])
            ),
        )

    a1_ranges = []
    sheet_name = target_sheet.properties.title
    grid_props = target_sheet.properties.gridProperties
    if grid_props:
        sheet_row_count = grid_props.rowCount
        sheet_col_count = grid_props.columnCount

        curr_range = calculate_a1_sheet_range(
            sheet_name,
            sheet_row_count,
            sheet_col_count,
            start_row,
            start_col,
            max_rows,
            max_cols,
        )
        if curr_range:
            a1_ranges.append(curr_range)

    # Next, get the data for the ranges
    if a1_ranges:
        response = (
            service.spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                includeGridData=True,
                ranges=a1_ranges,
                fields="spreadsheetId,spreadsheetUrl,properties/title,sheets/properties,sheets/data/rowData/values/userEnteredValue,sheets/data/rowData/values/formattedValue,sheets/data/rowData/values/effectiveValue",
            )
            .execute()
        )
    else:
        response = spreadsheet_with_only_metadata.model_dump()

    return parse_get_spreadsheet_response(response)


def process_get_spreadsheet_params(
    sheet_position: int | None,
    sheet_id_or_name: str | None,
    start_row: int,
    start_col: str,
    max_rows: int,
    max_cols: int,
) -> tuple[str, SheetIdentifierType, int, str, int, int]:
    """Process and validate the input parameters for the get_spreadsheet tool.

    Args:
        sheet_position (int | None): The position/tab of the sheet to get.
        sheet_id_or_name (str | None): The id or name of the sheet to get.
        start_row (int): Processed to be within the range [1, 1000]
        start_col (str): Processed to be alphabetic column representation. e.g., A, Z, QED
        max_rows (int): Processed to be within the range [1, 1000]
        max_cols (int): Processed to be within the range [1, 26]

    Returns:
        tuple[str, str, int, str, int, int]: The processed parameters.

    Raises:
        ToolExecutionError:
            If the start_col is not one of alphabetic or numeric
    """
    if sheet_id_or_name:
        sheet_identifier = sheet_id_or_name
        sheet_identifier_type = SheetIdentifierType.ID_OR_NAME
    elif sheet_position:
        sheet_identifier = str(sheet_position)
        sheet_identifier_type = SheetIdentifierType.POSITION
    else:
        raise RetryableToolError("Either sheet_position or sheet_id_or_name must be provided")

    processed_start_row = max(1, start_row)
    processed_max_rows = max(1, min(max_rows, 1000))
    processed_max_cols = max(1, min(max_cols, 26))
    if not all(c in string.ascii_letters for c in start_col):
        if not start_col.isdigit():
            raise ToolExecutionError("Input 'start_col' must be alphabetic (A-Z) or numeric")
        processed_start_col = index_to_col(int(start_col) - 1)
    else:
        processed_start_col = start_col.upper()

    return (
        sheet_identifier,
        sheet_identifier_type,
        processed_start_row,
        processed_start_col,
        processed_max_rows,
        processed_max_cols,
    )


def get_sheet_metadata_from_identifier(  # type: ignore[no-any-unimported]
    service: Resource,
    spreadsheet_id: str,
    sheet_position: int | None,
    sheet_id_or_name: str | None,
) -> tuple[str, int, str]:
    """Get the actual sheet name from position, id, or name identifier.

    Args:
        service (Resource): The Google Sheets service.
        spreadsheet_id (str): The ID of the spreadsheet.
        sheet_position (int | None): The position/tab of the sheet (1-indexed).
        sheet_id_or_name (str | None): The id or name of the sheet.

    Returns:
        tuple[str, str, str]: The sheet's title, id, and url.

    Raises:
        ToolExecutionError: If the sheet is not found.
    """
    # Determine the sheet identifier and type
    if sheet_id_or_name:
        sheet_identifier = sheet_id_or_name
        sheet_identifier_type = SheetIdentifierType.ID_OR_NAME
    elif sheet_position:
        sheet_identifier = str(sheet_position)
        sheet_identifier_type = SheetIdentifierType.POSITION
    else:
        # Default to first sheet
        sheet_identifier = "1"
        sheet_identifier_type = SheetIdentifierType.POSITION

    spreadsheet = get_spreadsheet_metadata_helper(service, spreadsheet_id)

    target_sheet = get_sheet_by_identifier(
        spreadsheet.sheets, sheet_identifier, sheet_identifier_type
    )

    if not target_sheet:
        raise ToolExecutionError(
            message=f"Sheet with {sheet_identifier_type.value} '{sheet_identifier}' not found",
            developer_message=(
                "Sheet(s) in the spreadsheet: "
                + ", ".join([sheet.properties.title for sheet in spreadsheet.sheets])
            ),
        )

    sheet_url = sheet_url_template.format(
        spreadsheet_id=spreadsheet_id,
        sheet_id=target_sheet.properties.sheetId,
    )

    return target_sheet.properties.title, target_sheet.properties.sheetId, sheet_url


def raise_for_large_payload(data: dict) -> None:
    """Enforce a 10MB limit on the data size.

    Args:
        data (dict): The data to enforce the size limit on.

    Raises:
        ToolExecutionError:
            If the data size exceeds 10MB
    """
    num_bytes = len(str(data).encode("utf-8"))

    if num_bytes >= (10 * 1024 * 1024):
        raise ToolExecutionError(
            message="Spreadsheet size exceeds 10MB limit. "
            "Please reduce the number of rows and columns you are requesting and try again.",
            developer_message=f"Data size: {num_bytes / 1024 / 1024:.4f}MB",
        )


# ------------------------------
# Search Utils
# ------------------------------
def build_files_list_query(
    mime_type: str,
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
) -> str:
    query = [f"(mimeType = '{mime_type}' and trashed = false)"]

    if isinstance(document_contains, str):
        document_contains = [document_contains]

    if isinstance(document_not_contains, str):
        document_not_contains = [document_not_contains]

    if document_contains:
        for keyword in document_contains:
            name_contains = keyword.replace("'", "\\'")
            full_text_contains = keyword.replace("'", "\\'")
            keyword_query = (
                f"(name contains '{name_contains}' or fullText contains '{full_text_contains}')"
            )
            query.append(keyword_query)

    if document_not_contains:
        for keyword in document_not_contains:
            name_not_contains = keyword.replace("'", "\\'")
            full_text_not_contains = keyword.replace("'", "\\'")
            keyword_query = (
                f"(not (name contains '{name_not_contains}' or "
                f"fullText contains '{full_text_not_contains}'))"
            )
            query.append(keyword_query)

    return " and ".join(query)


def build_files_list_params(
    mime_type: str,
    page_size: int,
    order_by: list[OrderBy] | None,
    pagination_token: str | None,
    include_shared_drives: bool,
    search_only_in_shared_drive_id: str | None,
    include_organization_domain_spreadsheets: bool,
    spreadsheet_contains: list[str] | None = None,
    spreadsheet_not_contains: list[str] | None = None,
) -> dict[str, Any]:
    query = build_files_list_query(
        mime_type=mime_type,
        document_contains=spreadsheet_contains,
        document_not_contains=spreadsheet_not_contains,
    )

    params = {
        "q": query,
        "pageSize": page_size,
        "orderBy": ",".join([item.value for item in order_by]) if order_by else None,
        "pageToken": pagination_token,
    }

    if (
        include_shared_drives
        or search_only_in_shared_drive_id
        or include_organization_domain_spreadsheets
    ):
        params["includeItemsFromAllDrives"] = "true"
        params["supportsAllDrives"] = "true"

    if search_only_in_shared_drive_id:
        params["driveId"] = search_only_in_shared_drive_id
        params["corpora"] = Corpora.DRIVE.value

    if include_organization_domain_spreadsheets:
        params["corpora"] = Corpora.DOMAIN.value

    params = remove_none_values(params)

    return params
