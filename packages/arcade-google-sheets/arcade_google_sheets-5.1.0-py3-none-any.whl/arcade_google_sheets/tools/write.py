from typing import Annotated

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google

from arcade_google_sheets.converters import SheetDataInputToValueRangesConverter
from arcade_google_sheets.models import (
    Spreadsheet,
    SpreadsheetProperties,
)
from arcade_google_sheets.utils import (
    batch_update,
    build_sheets_service,
    col_to_index,
    create_sheet,
    get_sheet_metadata_from_identifier,
    parse_write_to_cell_response,
    validate_sheet_data_input,
    validate_write_to_cell_params,
)


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
)
def create_spreadsheet(
    context: Context,
    title: Annotated[str, "The title of the new spreadsheet"] = "Untitled spreadsheet",
    data: Annotated[
        str | None,
        "The data to write to the spreadsheet. A JSON string "
        "(property names enclosed in double quotes) representing a dictionary that "
        "maps row numbers to dictionaries that map column letters to cell values. "
        "For example, data[23]['C'] would be the value of the cell in row 23, column C. "
        "Type hint: dict[int, dict[str, Union[int, float, str, bool]]]",
    ] = None,
) -> Annotated[dict, "The created spreadsheet's id and title"]:
    """Create a new spreadsheet with the provided title and data in its first sheet

    Returns the newly created spreadsheet's id and title
    """
    service = build_sheets_service(context.get_auth_token_or_empty())

    sheet_data = validate_sheet_data_input(data)

    spreadsheet = Spreadsheet(
        properties=SpreadsheetProperties(title=title),
        sheets=[create_sheet(sheet_data)],
    )

    body = spreadsheet.model_dump()

    response = (
        service.spreadsheets()
        .create(body=body, fields="spreadsheetId,spreadsheetUrl,properties/title")
        .execute()
    )

    return {
        "title": response["properties"]["title"],
        "spreadsheetId": response["spreadsheetId"],
        "spreadsheetUrl": response["spreadsheetUrl"],
    }


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
)
def write_to_cell(
    context: Context,
    spreadsheet_id: Annotated[str, "The id of the spreadsheet to write to"],
    column: Annotated[str, "The column string to write to. For example, 'A', 'F', or 'AZ'"],
    row: Annotated[int, "The row number to write to"],
    value: Annotated[str, "The value to write to the cell"],
    sheet_name: Annotated[
        str, "The name of the sheet to write to. Defaults to 'Sheet1'"
    ] = "Sheet1",
) -> Annotated[dict, "The status of the operation"]:
    """
    Write a value to a single cell in a spreadsheet.
    """
    service = build_sheets_service(context.get_auth_token_or_empty())
    validate_write_to_cell_params(service, spreadsheet_id, sheet_name, column, row)

    range_ = f"'{sheet_name}'!{column.upper()}{row}"
    body = {
        "range": range_,
        "majorDimension": "ROWS",
        "values": [[value]],
    }

    sheet_properties = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption="USER_ENTERED",
            includeValuesInResponse=True,
            body=body,
        )
        .execute()
    )

    return parse_write_to_cell_response(sheet_properties)


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
)
def update_cells(
    context: Context,
    spreadsheet_id: Annotated[str, "The id of the spreadsheet to write to"],
    data: Annotated[
        str,
        "The data to write. A JSON string (property names enclosed in double quotes) "
        "representing a dictionary that maps row numbers to dictionaries that map "
        "column letters to cell values. For example, data[23]['C'] is the value for cell C23. "
        "This is the same format accepted by create_spreadsheet. "
        "Type hint: dict[int, dict[str, int | float | str | bool]]",
    ],
    sheet_position: Annotated[
        int | None,
        "The position/tab of the sheet in the spreadsheet to write to. "
        "A value of 1 represents the first (leftmost/Sheet1) sheet. "
        "Defaults to 1.",
    ] = 1,
    sheet_id_or_name: Annotated[
        str | None,
        "The id or name of the sheet to write to. If provided, takes "
        "precedence over sheet_position.",
    ] = None,
) -> Annotated[dict, "The status of the operation, including updated ranges and counts"]:
    """
    Write values to a Google Sheet using a flexible data format.

    sheet_id_or_name takes precedence over sheet_position. If a sheet is not mentioned,
    then always assume the default sheet_position is sufficient.
    """
    service = build_sheets_service(context.get_auth_token_or_empty())

    sheet_data = validate_sheet_data_input(data)
    sheet_name, sheet_id, sheet_url = get_sheet_metadata_from_identifier(
        service, spreadsheet_id, sheet_position, sheet_id_or_name
    )
    converter = SheetDataInputToValueRangesConverter(sheet_name, sheet_data)
    value_ranges = converter.convert()

    response = batch_update(service, spreadsheet_id, value_ranges)

    return {**response, "sheet_url": sheet_url, "sheet_id": sheet_id}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
)
def add_note_to_cell(
    context: Context,
    spreadsheet_id: Annotated[str, "The id of the spreadsheet to add a comment to"],
    column: Annotated[str, "The column string to add a note to. For example, 'A', 'F', or 'AZ'"],
    row: Annotated[int, "The row number to add a note to"],
    note_text: Annotated[str, "The text for the note to add"],
    sheet_position: Annotated[
        int | None,
        "The position/tab of the sheet in the spreadsheet to write to. "
        "A value of 1 represents the first (leftmost/Sheet1) sheet. "
        "Defaults to 1.",
    ] = 1,
    sheet_id_or_name: Annotated[
        str | None,
        "The id or name of the sheet to write to. If provided, takes "
        "precedence over sheet_position.",
    ] = None,
) -> Annotated[dict, "The status of the operation"]:
    """
    Add a note to a specific cell in a spreadsheet. A note is a small
    piece of text attached to a cell (shown with a black triangle) that
    appears when you hover over the cell.

    sheet_id_or_name takes precedence over sheet_position. If a sheet is not mentioned,
    then always assume the default sheet_position is sufficient.
    """
    service = build_sheets_service(context.get_auth_token_or_empty())

    sheet_name, sheet_id, sheet_url = get_sheet_metadata_from_identifier(
        service, spreadsheet_id, sheet_position, sheet_id_or_name
    )
    column_index = col_to_index(column)

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row - 1,
                            "endRowIndex": row,
                            "startColumnIndex": column_index,
                            "endColumnIndex": column_index + 1,
                        },
                        "cell": {
                            "note": note_text,
                        },
                        "fields": "note",
                    },
                }
            ]
        },
    ).execute()

    return {
        "status": "success",
        "sheet_url": sheet_url,
        "sheet_id": sheet_id,
        "sheet_name": sheet_name,
    }
