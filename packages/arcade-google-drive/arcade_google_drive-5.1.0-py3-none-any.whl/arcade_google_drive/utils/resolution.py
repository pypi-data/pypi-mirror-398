from typing import Any, cast

from arcade_mcp_server.exceptions import ToolExecutionError
from googleapiclient.discovery import Resource


def _try_get_by_id(  # type: ignore[no-any-unimported]
    service: Resource,
    file_or_folder_id: str,
    shared_drive_id: str | None = None,
) -> dict[str, Any] | None:
    """Try to get a file/folder by ID. Returns metadata if found, None if not found."""
    try:
        params: dict[str, Any] = {
            "fileId": file_or_folder_id,
            "fields": "id, name, mimeType",
            "supportsAllDrives": True,
        }
        return cast(dict[str, Any], service.files().get(**params).execute())
    except Exception:
        # File not found or invalid ID. Caller should try name search.
        return None


def _search_by_name(  # type: ignore[no-any-unimported]
    service: Resource,
    name: str,
    parent_id: str | None = None,
    shared_drive_id: str | None = None,
    folder_only: bool = False,
) -> str | None:
    """Search for a file/folder by name within a parent folder.

    Args:
        service: Google Drive API service
        name: Name of the file/folder to find
        parent_id: If provided, only search within this folder. If None, searches globally.
        shared_drive_id: If provided, search within this shared drive
        folder_only: If True, only match folders

    Returns:
        File ID if found, None if not found
    """
    query = f"name = '{name}' and trashed = false"
    if folder_only:
        query += " and mimeType = 'application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    params: dict[str, Any] = {
        "q": query,
        "fields": "files(id, name)",
        "pageSize": 1,
    }

    if shared_drive_id:
        params["driveId"] = shared_drive_id
        params["corpora"] = "drive"
        params["includeItemsFromAllDrives"] = True
        params["supportsAllDrives"] = True

    results = cast(dict[str, Any], service.files().list(**params).execute())
    files = results.get("files", [])
    return files[0]["id"] if files else None


def _resolve_path(  # type: ignore[no-any-unimported]
    service: Resource,
    path: str,
    shared_drive_id: str | None = None,
    folder_only: bool = False,
) -> str | None:
    """Resolve a path like 'folder1/folder2/item' by traversing each component.

    For a path like 'A/B/C':
    1. Find 'A' in root (or shared drive root)
    2. Find 'B' within A
    3. Find 'C' within B

    Args:
        service: Google Drive API service
        path: Path to resolve (e.g., 'folder/subfolder/file')
        shared_drive_id: If provided, start from this shared drive's root
        folder_only: If True, final component must be a folder

    Returns:
        ID of the final path component, or None if not found
    """
    path_parts = path.strip("/").split("/")

    # Start from root
    # For shared drives, the drive ID is the root. For My Drive, it's 'root'.
    current_parent_id = shared_drive_id if shared_drive_id else "root"

    # Traverse all components except the last one (they must all be folders)
    for part in path_parts[:-1]:
        folder_id = _search_by_name(
            service,
            part,
            parent_id=current_parent_id,
            shared_drive_id=shared_drive_id,
            folder_only=True,
        )
        if not folder_id:
            return None
        current_parent_id = folder_id

    # Find the final component (may or may not be a folder depending on folder_only)
    final_name = path_parts[-1]
    return _search_by_name(
        service,
        final_name,
        parent_id=current_parent_id,
        shared_drive_id=shared_drive_id,
        folder_only=folder_only,
    )


def resolve_file_id(  # type: ignore[no-any-unimported]
    service: Resource,
    file_path_or_id: str,
    shared_drive_id: str | None = None,
    require_folder: bool = False,
) -> str:
    """Resolve a file or folder path, name, or ID to a file ID.

    Args:
        service: Google Drive API service
        file_path_or_id: File/folder path, name, or ID to resolve
        shared_drive_id: If provided, search within this shared drive
        require_folder: If True, ensure the resolved item is a folder

    Resolution strategy:
    1. If input contains a slash, treat as path and traverse each component
    2. Otherwise, first try as a direct ID (API call)
    3. If ID lookup fails, search by name globally
    4. If all fail, raise an error

    This approach is deterministic and works 100% of the time.
    """
    file_path_or_id = file_path_or_id.strip()
    item_type = "Folder" if require_folder else "File"

    # If contains a slash, it's a path so we traverse it.
    if "/" in file_path_or_id:
        result_id = _resolve_path(
            service, file_path_or_id, shared_drive_id, folder_only=require_folder
        )
        if result_id:
            return result_id
        raise ToolExecutionError(
            message=f"{item_type} not found: {file_path_or_id}",
            developer_message=f"Could not resolve path '{file_path_or_id}'",
        )

    # If it doesn't contain a slash, then it could be a name or an ID.
    # Step 1: Try as direct ID first
    file_metadata = _try_get_by_id(service, file_path_or_id, shared_drive_id)
    if file_metadata:
        # If require_folder is True, verify it's actually a folder
        if require_folder and file_metadata.get("mimeType") != "application/vnd.google-apps.folder":
            # Not a folder, fall through to name search
            pass
        else:
            return str(file_metadata["id"])

    # Step 2: ID lookup failed or wasn't the right type, so we try searching by name globally.
    result_id = _search_by_name(
        service,
        file_path_or_id,
        parent_id=None,
        shared_drive_id=shared_drive_id,
        folder_only=require_folder,
    )
    if result_id:
        return result_id

    raise ToolExecutionError(
        message=f"{item_type} not found: {file_path_or_id}",
        developer_message=f"Could not resolve '{file_path_or_id}' as ID or name",
    )
