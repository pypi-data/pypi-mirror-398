from typing import Annotated

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google

from arcade_google_sheets.templates import sheet_url_template
from arcade_google_sheets.utils import (
    build_sheets_service,
    get_spreadsheet_metadata_helper,
    get_spreadsheet_with_pagination,
    process_get_spreadsheet_params,
    raise_for_large_payload,
)


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    ),
)
async def get_spreadsheet(
    context: Context,
    spreadsheet_id: Annotated[str, "The id of the spreadsheet to get"],
    sheet_position: Annotated[
        int | None,
        "The position/tab of the sheet in the spreadsheet to get. "
        "A value of 1 represents the first (leftmost/Sheet1) sheet . "
        "Defaults to 1.",
    ] = 1,
    sheet_id_or_name: Annotated[
        str | None,
        "The id or name of the sheet to get. "
        "Defaults to None, which means sheet_position will be used instead.",
    ] = None,
    start_row: Annotated[int, "Starting row number (1-indexed, defaults to 1)"] = 1,
    start_col: Annotated[
        str, "Starting column letter(s) or 1-based column number (defaults to 'A')"
    ] = "A",
    max_rows: Annotated[
        int,
        "Maximum number of rows to fetch for each sheet in the spreadsheet. "
        "Must be between 1 and 1000. Defaults to 1000.",
    ] = 1000,
    max_cols: Annotated[
        int,
        "Maximum number of columns to fetch for each sheet in the spreadsheet. "
        "Must be between 1 and 100. Defaults to 100.",
    ] = 100,
) -> Annotated[
    dict,
    "The spreadsheet properties and data for the specified sheet in the spreadsheet",
]:
    """Gets the specified range of cells from a single sheet in the spreadsheet.

    sheet_id_or_name takes precedence over sheet_position. If a sheet is not mentioned,
    then always assume the default sheet_position is sufficient.
    """
    sheet_identifier, sheet_identifier_type, start_row, start_col, max_rows, max_cols = (
        process_get_spreadsheet_params(
            sheet_position,
            sheet_id_or_name,
            start_row,
            start_col,
            max_rows,
            max_cols,
        )
    )

    service = build_sheets_service(context.get_auth_token_or_empty())

    data = get_spreadsheet_with_pagination(
        service,
        spreadsheet_id,
        sheet_identifier,
        sheet_identifier_type,
        start_row,
        start_col,
        max_rows,
        max_cols,
    )

    raise_for_large_payload(data)
    return data


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    ),
)
async def get_spreadsheet_metadata(
    context: Context,
    spreadsheet_id: Annotated[str, "The id of the spreadsheet to get metadata for"],
) -> Annotated[dict, "The spreadsheet metadata for the specified spreadsheet"]:
    """Gets the metadata for a spreadsheet including the metadata for the sheets in the spreadsheet.

    Use this tool to get the name, position, ID, and URL of all sheets in a spreadsheet as well as
    the number of rows and columns in each sheet.

    Does not return the content/data of the sheets in the spreadsheet - only the metadata.
    Excludes spreadsheets that are in the trash.
    """
    service = build_sheets_service(context.get_auth_token_or_empty())

    metadata = get_spreadsheet_metadata_helper(service, spreadsheet_id)
    metadata_dict = metadata.model_dump(exclude_none=True)
    for sheet in metadata_dict.get("sheets") or []:
        sheet["sheet_url"] = sheet_url_template.format(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet["properties"]["sheetId"],
        )

    return {
        "spreadsheet_title": metadata_dict["properties"]["title"],
        "spreadsheet_id": metadata_dict["spreadsheetId"],
        "spreadsheet_url": metadata_dict["spreadsheetUrl"],
        "sheets": metadata_dict.get("sheets") or [],
    }
