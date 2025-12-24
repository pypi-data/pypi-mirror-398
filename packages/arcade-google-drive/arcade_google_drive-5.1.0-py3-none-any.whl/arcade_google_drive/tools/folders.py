from typing import Annotated, Any

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_google_drive.tool_responses import CreateFolderResponse
from arcade_google_drive.utils.drive_client import build_drive_service
from arcade_google_drive.utils.resolution import resolve_file_id


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/drive.file"]))
async def create_folder(
    context: Context,
    folder_name: Annotated[
        str,
        "The name of the new folder to create",
    ],
    parent_folder_path_or_id: Annotated[
        str | None,
        "The parent folder path like folder/subfolder or folder ID where to create. "
        "If None, creates at the root of My Drive. If providing a path, it will be "
        "resolved within My Drive by default. Do not include the folder to create in this path. "
        "Defaults to None.",
    ] = None,
    shared_drive_id: Annotated[
        str | None,
        "If creating in a shared drive and using a parent folder path, "
        "provide the shared drive ID. Not needed when using folder IDs or "
        "creating in My Drive. Defaults to None.",
    ] = None,
) -> Annotated[
    CreateFolderResponse,
    "Created folder information including ID, name, web view link, and location path",
]:
    """Create a new folder in Google Drive.

    By default, parent folder paths are resolved in My Drive. For shared drives, use folder IDs
    or provide shared_drive_id."""
    service = build_drive_service(context.get_auth_token_or_empty())

    if not folder_name or not folder_name.strip():
        raise ToolExecutionError(
            message="Folder name cannot be empty",
            developer_message="The folder_name parameter must be a non-empty string",
        )

    file_metadata: dict[str, Any] = {
        "name": folder_name.strip(),
        "mimeType": "application/vnd.google-apps.folder",
    }

    if parent_folder_path_or_id:
        parent_id = resolve_file_id(
            service, parent_folder_path_or_id, shared_drive_id, require_folder=True
        )
        file_metadata["parents"] = [parent_id]

    params: dict[str, Any] = {
        "body": file_metadata,
        "fields": "id, name, mimeType, parents, webViewLink",
    }

    if shared_drive_id:
        params["supportsAllDrives"] = True

    result = service.files().create(**params).execute()

    response: CreateFolderResponse = {
        "id": result["id"],
        "name": result["name"],
        "mimeType": result["mimeType"],
        "parents": result.get("parents", []),
        "webViewLink": result.get("webViewLink", ""),
    }
    return response
