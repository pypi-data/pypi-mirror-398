from typing import Annotated, Any

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google

from arcade_google_sheets.enums import OrderBy
from arcade_google_sheets.templates import (
    spreadsheet_url_template,
)
from arcade_google_sheets.utils import (
    build_drive_service,
    build_files_list_params,
    remove_none_values,
)


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    ),
)
async def search_spreadsheets(
    context: Context,
    spreadsheet_contains: Annotated[
        list[str] | None,
        "Keywords or phrases that must be in the spreadsheet title. Provide a list of "
        "keywords or phrases if needed.",
    ] = None,
    spreadsheet_not_contains: Annotated[
        list[str] | None,
        "Keywords or phrases that must NOT be in the spreadsheet title. Provide a list of "
        "keywords or phrases if needed.",
    ] = None,
    search_only_in_shared_drive_id: Annotated[
        str | None,
        "The ID of the shared drive to restrict the search to. If provided, the search will only "
        "return spreadsheets from this drive. Defaults to None, which searches across all drives.",
    ] = None,
    include_shared_drives: Annotated[
        bool,
        "Whether to include spreadsheets from shared drives. Defaults to False (searches only in "
        "the user's 'My Drive').",
    ] = False,
    include_organization_domain_spreadsheets: Annotated[
        bool,
        "Whether to include spreadsheets from the organization's domain. "
        "This is applicable to admin users who have permissions to view "
        "organization-wide spreadsheets in a Google Workspace account. "
        "Defaults to False.",
    ] = False,
    order_by: Annotated[
        list[OrderBy] | None,
        "Sort order. Defaults to listing the most recently modified spreadsheets first. "
        "If spreadsheet_contains or spreadsheet_not_contains is provided, "
        "then the order_by will be ignored.",
    ] = None,
    limit: Annotated[
        int, "The maximum number of spreadsheets to list. Defaults to 10. Max is 50"
    ] = 10,
    pagination_token: Annotated[
        str | None, "The pagination token to continue a previous request"
    ] = None,
) -> Annotated[
    dict,
    "A dictionary containing the title, ID, and URL for each matching spreadsheet. "
    "Also contains a pagination token if there are more spreadsheets to list.",
]:
    """
    Searches for spreadsheets in the user's Google Drive based on the titles and content and
    returns the title, ID, and URL for each matching spreadsheet.

    Does not return the content/data of the sheets in the spreadsheets - only the metadata.
    Excludes spreadsheets that are in the trash.
    """
    if spreadsheet_contains or spreadsheet_not_contains:
        # Google drive API does not support other order_by values for
        # queries with fullText search (which is used when spreadsheet_contains
        # or spreadsheet_not_contains is provided).
        order_by = None
    if order_by is None:
        order_by = [OrderBy.MODIFIED_TIME_DESC]
    elif isinstance(order_by, OrderBy):
        order_by = [order_by]

    limit = max(1, min(50, limit))
    page_size = min(10, limit)
    spreadsheets: list[dict[str, Any]] = []

    drive_service = build_drive_service(context.get_auth_token_or_empty())

    params = build_files_list_params(
        mime_type="application/vnd.google-apps.spreadsheet",
        page_size=page_size,
        order_by=order_by,
        pagination_token=pagination_token,
        include_shared_drives=include_shared_drives,
        search_only_in_shared_drive_id=search_only_in_shared_drive_id,
        include_organization_domain_spreadsheets=include_organization_domain_spreadsheets,
        spreadsheet_contains=spreadsheet_contains,
        spreadsheet_not_contains=spreadsheet_not_contains,
    )

    while len(spreadsheets) < limit:
        if pagination_token:
            params["pageToken"] = pagination_token
        else:
            params.pop("pageToken", None)

        results = drive_service.files().list(**params).execute()
        batch = results.get("files") or []
        if not isinstance(batch, list):
            batch = []
        spreadsheets.extend(batch[: limit - len(spreadsheets)])

        pagination_token = results.get("nextPageToken")
        if not pagination_token or len(batch) < page_size:
            break

    # Add the spreadsheet URL to each spreadsheet
    for spreadsheet in spreadsheets:
        spreadsheet["url"] = spreadsheet_url_template.format(spreadsheet_id=spreadsheet["id"])

    tool_response = {
        "pagination_token": pagination_token,
        "spreadsheets_count": len(spreadsheets),
        "spreadsheets": spreadsheets,
    }
    tool_response = remove_none_values(tool_response)

    return tool_response
