from typing import Any, cast

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from arcade_google_drive.tool_responses import WhoAmIResponse


def build_who_am_i_response(context: Any, drive_service: Any) -> WhoAmIResponse:
    """Build complete who_am_i response from Google Drive and People APIs."""
    credentials = Credentials(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )
    people_service = _build_people_service(credentials)
    person = _get_people_api_data(people_service)

    user_info = _extract_profile_data(person)
    user_info.update(_extract_google_drive_info(drive_service))

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
        if primary_emails:
            profile_data["my_email_address"] = primary_emails[0].get("value")

    return profile_data


def _extract_google_drive_info(drive_service: Any) -> dict[str, Any]:
    """Extract Google Drive specific information."""
    drive_info: dict[str, Any] = {}

    try:
        # Get Drive about info including storage quota and user info
        about_info = (
            drive_service.about()
            .get(fields="user,storageQuota,canCreateDrives,canCreateTeamDrives")
            .execute()
        )
        drive_info["google_drive_access"] = True
        drive_info["drive_about_info"] = about_info.get("user", {})
        drive_info["drive_storage_quota"] = about_info.get("storageQuota", {})

        # Get file count (limited to first 1000 for performance)
        files_result = drive_service.files().list(pageSize=1000, fields="files(id)").execute()
        drive_info["drive_files_count"] = len(files_result.get("files", []))

        # Get shared drives count
        try:
            shared_drives_result = (
                drive_service.drives().list(pageSize=100, fields="drives(id,name)").execute()
            )
            shared_drives = shared_drives_result.get("drives", [])
            if not isinstance(shared_drives, list):
                shared_drives = []
            drive_info["shared_drives"] = shared_drives
            drive_info["drive_shared_drives_count"] = len(shared_drives)
        except Exception:
            drive_info["drive_shared_drives_count"] = 0
            drive_info["shared_drives"] = []

    except Exception:
        drive_info["google_drive_access"] = False
        drive_info["drive_files_count"] = 0
        drive_info["drive_shared_drives_count"] = 0
        drive_info["shared_drives"] = []

    return drive_info


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
