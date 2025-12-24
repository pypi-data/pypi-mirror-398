from enum import Enum

from typing_extensions import TypedDict


class GoogleDriveFileType(str, Enum):
    """
    https://developers.google.com/workspace/drive/api/guides/mime-types
    """

    SPREADSHEET = "spreadsheet"
    SLIDES = "slides"
    DOCUMENT = "document"
    DRAWING = "drawing"
    FORM = "form"
    FOLDER = "folder"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    SCRIPT = "script"
    SITES = "sites"
    PDF = "pdf"


def get_google_drive_mime_type(file_type: GoogleDriveFileType) -> list[str]:
    """Get the Google Drive mime type from the file type string."""
    return {
        GoogleDriveFileType.SPREADSHEET: ["application/vnd.google-apps.spreadsheet"],
        GoogleDriveFileType.SLIDES: ["application/vnd.google-apps.presentation"],
        GoogleDriveFileType.DOCUMENT: ["application/vnd.google-apps.document"],
        GoogleDriveFileType.DRAWING: ["application/vnd.google-apps.drawing"],
        GoogleDriveFileType.FORM: ["application/vnd.google-apps.form"],
        GoogleDriveFileType.FOLDER: ["application/vnd.google-apps.folder"],
        GoogleDriveFileType.IMAGE: ["image/jpeg", "image/png", "image/gif", "image/webp"],
        GoogleDriveFileType.VIDEO: [
            "video/mp4",
            "video/mpeg",
            "video/quicktime",
            "video/webm",
        ],
        GoogleDriveFileType.AUDIO: [
            "audio/mpeg",
            "audio/mp3",
            "audio/mp4",
            "audio/m4a",
            "audio/wav",
            "video/ogg",
        ],
        GoogleDriveFileType.SCRIPT: ["application/vnd.google-apps.script"],
        GoogleDriveFileType.SITES: ["application/vnd.google-apps.sites"],
        GoogleDriveFileType.PDF: ["application/pdf"],
    }[file_type]


class GoogleDriveFile(TypedDict, total=False):
    """
    Raw Google Drive file object from API response.

    Example:
    {
        'parents': ['0AKjrBWHCHoQIUk9PVA'],
        'owners': [{'displayName': 'Evan Tahler', 'kind': 'drive#user', 'me': True, 'permissionId': '01977551318624746334', 'emailAddress': 'evan@arcade.dev', 'photoLink': 'https://lh3.googleusercontent.com/a-/ALV-UjWzhqbI7gjHCLmIrI_vYWJFZrdzxFqK-gbLELyADCyApxmLgsUFhvyqAMLm5jC9Ech4H0hrimnbwTnrg3eZP8Ok3NHIESLr78pT6DCg1VZcimaxwoRbyMVvQHrBeasbsBmzJoSiOdHCWN9YMPuuO853c-l1YUJwc88m5N0d2dNoFPz9awg-bfDMVnC3PVoMEqq8cmOX4JKNsw5qeSJ1EkwC1fu2WyQp683oCc6oMk1LwUIy5T24Yxv6v8_UGXUTLCWCD22pN-uq_o-DpaPew3OLlW-rQqPBlpB9EU70FeHW50dJuRZC8mc5WuCVp1TVCdy_ZkSfoOLn5KlTbuMxh29iiDo3OsJxu3kGO23Yi_REXj7RiewqzebuHNtvvajNElGM-7RcGNTVX5PZlhS3U95tp0GuvPFI6uhihRD5Y1GimRez_2whMW3yrfGDRmjJA2qyuXVTmWKAzE5aKUX_8KJwXp0eEoraqwY7zOK-Gt-1ZZwZ3j0J_iUo5BtZ39QBksqxG3OFwuFWR9VXsfbu5WNCgO0p4z_oIucNFqhiMT4NpzrbkknQpuOe3cf0MJXAK5IuWVDsBR2AckaeuACdMlODct-X1RRKpRtNUFsrNJRVUMwmscGiSonevaukHG4ddAtAPLgAX14JYUUQch8XbmCRjf5mpdxwbqrlC6iSwqmydhzznyw-EYY_2X9hj5-yw1HN0fzfSCbfTET6AwjZJoYqGyXP7sCUfIRtWEeQinkszPSU69uLKXQGLWWTtAdkLzifnixh9hNONP8vfVq_3blmgLlxj8y2NweBDeCTV9RA53DWleDh41aUOU45BPgrOtYzSbUJ_ih9KvDKNSbzyPEWYi6mBi9n16vs2S57Fg1UX_g_XbAGH2qGKWtxjZ2zeTtKEiBv01GBr6-HmuUmkTezcKNc4g12hadwJOdZImusy-xC062E5msrjc0rDDvTeoxCxRthPwR6zNQ0xzyAKPKZUTCE-g=s64'}],
        'id': '1wZi1yKWKOyg1dpueA2eBvTtYlUjqqp7e_M1nuAoF8NY',
        'name': 'Blog Post: Designing SQL Tools for AI Agents',
        'mimeType': 'application/vnd.google-apps.document',
        'webViewLink': 'https://docs.google.com/document/1wZi1yKWKOyg1dpueA2eBvTtYlUjqqp7e_M1nuAoF8NY/edit?usp=drivesdk',
        'thumbnailLink': 'https://lh3.googleusercontent.com/drive-storage/AJQWtBPaGDAR8YRloXrj88Y4A_xCmttab-wQUKvvx3Y_mcV8-7rYNAEBopZ0_W9P9Bs8uDQp4OfFJRv08OVBX02kuBkbBZKGONANk2Gc2sgfUpaXZi8bmFuF3osKX4MB=s220',
        'createdTime': '2025-07-14T22:22:48.423Z',
        'modifiedTime': '2025-07-23T01:48:23.159Z',
        'size': '1214637'}
    """  # noqa: E501

    # owners: list[GoogleDriveFileOwner]
    parents: list[str]
    id: str
    name: str
    mimeType: str
    webViewLink: str
    createdTime: str
    modifiedTime: str

    # Only for non-folder files
    thumbnailLink: str
    size: str


class SearchMetadata(TypedDict, total=False):
    """Metadata about the search operation."""

    file_types_filtered: list[GoogleDriveFileType] | None
    include_shared_drives: bool
    order_by: str | None


class SearchResult(TypedDict, total=False):
    """Result of a Google Drive search operation."""

    query: str
    search_query: str
    total_results: int
    files: list[GoogleDriveFile]
    search_metadata: SearchMetadata
