from typing import Annotated

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google

from arcade_google_drive.tool_responses import WhoAmIResponse
from arcade_google_drive.utils.drive_client import build_drive_service
from arcade_google_drive.utils.who_am_i import build_who_am_i_response


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
    WhoAmIResponse,
    "Get comprehensive user profile and Google Drive environment information.",
]:
    """
    Get comprehensive user profile and Google Drive environment information.

    This tool provides detailed information about the authenticated user including
    their name, email, profile picture, Google Drive storage information, the shared
    drives (and their IDs) the user has access to, and other
    important profile details from Google services.
    """
    drive_service = build_drive_service(context.get_auth_token_or_empty())
    response: WhoAmIResponse = build_who_am_i_response(context, drive_service)

    return response
