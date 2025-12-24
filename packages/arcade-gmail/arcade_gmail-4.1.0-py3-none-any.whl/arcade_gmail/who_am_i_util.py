from typing import Any, cast

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing_extensions import TypedDict


class WhoAmIResponse(TypedDict, total=False):
    my_email_address: str
    messages_total: int
    threads_total: int
    history_id: str
    display_name: str
    given_name: str
    family_name: str
    formatted_name: str
    profile_picture_url: str


def build_who_am_i_response(context: Any, gmail_service: Any) -> WhoAmIResponse:
    """Build complete who_am_i response from Gmail and People APIs."""
    gmail_profile = gmail_service.users().getProfile(userId="me").execute()

    credentials = Credentials(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )
    people_service = _build_people_service(credentials)
    person = _get_people_api_data(people_service)

    user_info = _extract_gmail_profile_data(gmail_profile)
    profile_data = _extract_profile_data(person)
    # Don't override Gmail's email address
    if "my_email_address" in profile_data and "my_email_address" in user_info:
        del profile_data["my_email_address"]
    user_info.update(profile_data)

    return cast(WhoAmIResponse, user_info)


def _extract_profile_data(person: dict[str, Any]) -> dict[str, Any]:
    """Extract user profile data from People API response."""
    profile_data = {}

    names = person.get("names", [])
    if names:
        primary_name = names[0]
        profile_data.update({
            "display_name": primary_name.get("displayName"),
            "given_name": primary_name.get("givenName"),
            "family_name": primary_name.get("familyName"),
            "formatted_name": primary_name.get("displayNameLastFirst"),
        })

    photos = person.get("photos", [])
    if photos:
        profile_data["profile_picture_url"] = photos[0].get("url")

    email_addresses = person.get("emailAddresses", [])
    if email_addresses:
        primary_emails = [
            email for email in email_addresses if email.get("metadata", {}).get("primary")
        ]
        if primary_emails and "my_email_address" not in profile_data:
            profile_data["my_email_address"] = primary_emails[0].get("value")

    return profile_data


def _extract_gmail_profile_data(gmail_profile: dict[str, Any]) -> dict[str, Any]:
    """Extract Gmail profile data from Gmail API response."""
    return {
        "my_email_address": gmail_profile.get("emailAddress"),
        "messages_total": gmail_profile.get("messagesTotal", 0),
        "threads_total": gmail_profile.get("threadsTotal", 0),
        "history_id": gmail_profile.get("historyId"),
    }


def _build_people_service(credentials: Credentials) -> Any:
    """Build and return the People API service client."""
    return build("people", "v1", credentials=credentials)


def _get_people_api_data(people_service: Any) -> dict[str, Any]:
    """Get user profile information from People API."""
    person_fields = "names,emailAddresses,photos"
    return cast(
        dict[str, Any],
        people_service.people().get(resourceName="people/me", personFields=person_fields).execute(),
    )
