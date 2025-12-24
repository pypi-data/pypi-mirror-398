from typing import Any

from typing_extensions import TypedDict

from arcade_google_drive.models import GoogleDriveFile, SearchMetadata


class SearchFilesResponse(TypedDict, total=False):
    """Response from the search_files tool."""

    query: str
    search_query: str
    total_results: int
    files: list[GoogleDriveFile]
    search_metadata: SearchMetadata


class SharePermission(TypedDict, total=False):
    """A single permission granted when sharing a file."""

    id: str
    type: str
    role: str
    emailAddress: str


class ShareFileResponse(TypedDict, total=False):
    """Response from the share_file tool."""

    fileId: str
    permissions: list[SharePermission]


class CreateFolderResponse(TypedDict, total=False):
    """Response from the create_folder tool."""

    id: str
    name: str
    mimeType: str
    parents: list[str]
    webViewLink: str


class FileTreeDrive(TypedDict, total=False):
    """A drive in the file tree structure.

    children contains nested file/folder nodes, each with name, id, type, and optional children.
    """

    name: str
    id: str
    children: list[dict[str, Any]]


class GetFileTreeStructureResponse(TypedDict, total=False):
    """Response from the get_file_tree_structure tool."""

    drives: list[FileTreeDrive]


class GenerateGoogleFilePickerUrlResponse(TypedDict, total=False):
    """Response from the generate_google_file_picker_url tool."""

    url: str
    llm_instructions: str


class WhoAmIResponse(TypedDict, total=False):
    """Response from the who_am_i tool."""

    my_email_address: str
    display_name: str
    given_name: str
    family_name: str
    formatted_name: str
    profile_picture_url: str
    google_drive_access: bool
    drive_storage_quota: dict[str, str | int]
    drive_about_info: dict[str, Any]
    drive_files_count: int
    drive_shared_drives_count: int
    shared_drives: list[dict[str, str]]


class RenameFileResponse(TypedDict, total=False):
    """Response from the rename_file tool."""

    id: str
    name: str
    webViewLink: str


class MoveFileResponse(TypedDict, total=False):
    """Response from the move_file tool."""

    id: str
    name: str
    parents: list[str]
    webViewLink: str


class DownloadFileResponse(TypedDict, total=False):
    """Response from the download_file tool.

    For small files: returns id, name, mimeType, size, and content.
    For large files: returns id, name, mimeType, size, requires_chunked_download=True,
    total_size_bytes, recommended_chunk_size, and message with instructions.
    """

    id: str
    name: str
    mimeType: str
    size: int
    # Small file fields
    content: str
    # Large file (chunked download) fields
    requires_chunked_download: bool
    total_size_bytes: int
    recommended_chunk_size: int
    message: str


class DownloadFileChunkResponse(TypedDict, total=False):
    """Response from the download_file_chunk tool."""

    id: str
    name: str
    mimeType: str
    chunk_start_byte: int
    chunk_end_byte: int
    chunk_size: int
    total_size_bytes: int
    content: str
    is_final_chunk: bool
    next_start_byte: int | None
    progress_percent: float


class UploadFileResponse(TypedDict, total=False):
    """Response from the upload_file tool."""

    id: str
    name: str
    mimeType: str
    parents: list[str]
    webViewLink: str
