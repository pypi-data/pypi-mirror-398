from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build


def build_drive_service(auth_token: str) -> Resource:  # type: ignore[no-any-unimported]
    """Build a Google Drive API service object.

    Args:
        auth_token: OAuth2 access token for authentication

    Returns:
        Google Drive API service resource
    """
    return build("drive", "v3", credentials=Credentials(auth_token))
