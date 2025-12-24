from typing import Annotated, Any

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google

from arcade_google_sheets.utils import build_sheets_service
from arcade_google_sheets.who_am_i_util import build_who_am_i_response


@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ]
    )
)
async def who_am_i(
    context: Context,
) -> Annotated[
    dict[str, Any],
    "Get comprehensive user profile and Google Sheets environment information.",
]:
    """
    Get comprehensive user profile and Google Sheets environment information.

    This tool provides detailed information about the authenticated user including
    their name, email, profile picture, Google Sheets access permissions, and other
    important profile details from Google services.
    """

    auth_token = context.get_auth_token_or_empty()
    sheets_service = build_sheets_service(auth_token)
    user_info = build_who_am_i_response(context, sheets_service)

    return dict(user_info)
