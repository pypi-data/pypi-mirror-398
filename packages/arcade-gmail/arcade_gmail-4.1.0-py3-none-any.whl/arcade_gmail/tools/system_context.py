from typing import Annotated, Any

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google

from arcade_gmail.client import GmailClient
from arcade_gmail.who_am_i_util import build_who_am_i_response


@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ]
    )
)
async def who_am_i(
    context: Context,
) -> Annotated[
    dict[str, Any],
    "Get comprehensive user profile and Gmail account information.",
]:
    """
    Get comprehensive user profile and Gmail account information.

    This tool provides detailed information about the authenticated user including
    their name, email, profile picture, Gmail account statistics, and other
    important profile details from Google services.
    """

    client = GmailClient(context)
    user_info = build_who_am_i_response(context, client.service)

    return dict(user_info)
