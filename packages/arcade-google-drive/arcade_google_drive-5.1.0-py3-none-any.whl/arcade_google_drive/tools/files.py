import io
from typing import Annotated, Any

import httpx
from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google
from arcade_mcp_server.exceptions import RetryableToolError, ToolExecutionError
from googleapiclient.http import MediaIoBaseUpload

from arcade_google_drive.constants import (
    DEFAULT_CHUNK_SIZE_BYTES,
    MAX_CHUNK_SIZE_BYTES,
    MAX_RESPONSE_CONTENT_BYTES,
    MAX_SIMPLE_UPLOAD_BYTES,
    UPLOAD_TIMEOUT,
)
from arcade_google_drive.enums import UploadMimeType
from arcade_google_drive.tool_responses import (
    DownloadFileChunkResponse,
    DownloadFileResponse,
    MoveFileResponse,
    RenameFileResponse,
    UploadFileResponse,
)
from arcade_google_drive.utils.content import encode_content, fetch_from_url, infer_mime_type
from arcade_google_drive.utils.drive_client import (
    build_drive_service,
)
from arcade_google_drive.utils.resolution import resolve_file_id
from arcade_google_drive.utils.resumable_upload import upload_file_resumable


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/drive.file"]))
async def rename_file(
    context: Context,
    file_path_or_id: Annotated[
        str,
        "The path like folder/subfolder/filename or the file ID to rename. "
        "If providing a path, it will be resolved within 'My Drive' by default.",
    ],
    new_filename: Annotated[
        str,
        "The new name for the file",
    ],
    shared_drive_id: Annotated[
        str | None,
        "If the file is in a shared drive and you're using a path (not ID), provide the shared "
        "drive ID to resolve the path within that drive. Not needed when using file IDs. "
        "Defaults to None (searches 'My Drive').",
    ] = None,
) -> Annotated[
    RenameFileResponse,
    "Confirmation with the file's new name, ID, and web view link",
]:
    """Rename a file or folder in Google Drive.

    By default, paths are resolved in My Drive. For files in shared drives, either use the file ID
    directly or provide the shared_drive_id parameter."""
    service = build_drive_service(context.get_auth_token_or_empty())
    file_id = resolve_file_id(service, file_path_or_id, shared_drive_id)

    params: dict[str, Any] = {
        "fileId": file_id,
        "body": {"name": new_filename},
        "fields": "id, name, webViewLink",
    }
    if shared_drive_id:
        params["supportsAllDrives"] = True

    result = service.files().update(**params).execute()

    response: RenameFileResponse = {
        "id": result["id"],
        "name": result["name"],
        "webViewLink": result.get("webViewLink", ""),
    }
    return response


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/drive.file"]))
async def move_file(
    context: Context,
    source_file_path_or_id: Annotated[
        str,
        "The source file path like folder/subfolder/filename or the file ID "
        "of the file to move. If providing a path, it will be resolved within "
        "'My Drive' by default.",
    ],
    destination_folder_path_or_id: Annotated[
        str | None,
        "The path to the file's parent folder (exclude the file to be moved) or parent folder ID "
        "to move the file into. If None, moves to the root of the drive. Defaults to None.",
    ] = None,
    new_filename: Annotated[
        str | None,
        "Optional new name for the file after moving. If None, keeps the original name. "
        "Defaults to None.",
    ] = None,
    shared_drive_id: Annotated[
        str | None,
        "If working with paths in a shared drive, provide the shared drive ID. "
        "Not needed when using IDs. Defaults to None (uses My Drive).",
    ] = None,
) -> Annotated[
    MoveFileResponse,
    "Confirmation with the file's ID, name, and new location",
]:
    """Move a file or folder to a different folder within the same Google Drive.

    Can move to a folder (keeping name), or move and rename in one operation. By default, paths
    are resolved in My Drive. For shared drives, use file IDs or provide shared_drive_id.
    """
    service = build_drive_service(context.get_auth_token_or_empty())
    file_id = resolve_file_id(service, source_file_path_or_id, shared_drive_id)

    # Handle root directory case
    if destination_folder_path_or_id is None or destination_folder_path_or_id.strip() in (
        "",
        "/",
        "root",
        "root/",
    ):
        # For My Drive, use "root". For shared drives, use the drive ID as the root.
        dest_folder_id = shared_drive_id if shared_drive_id else "root"
    else:
        dest_folder_id = resolve_file_id(
            service, destination_folder_path_or_id, shared_drive_id, require_folder=True
        )

    # Get current file info to find current parent
    current_file = service.files().get(fileId=file_id, fields="id, name, parents").execute()
    current_parents = ",".join(current_file.get("parents", []))

    params: dict[str, Any] = {
        "fileId": file_id,
        "addParents": dest_folder_id,
        "removeParents": current_parents,
        "fields": "id, name, parents, webViewLink",
    }
    if new_filename:
        params["body"] = {"name": new_filename}
    if shared_drive_id:
        params["supportsAllDrives"] = True

    result = service.files().update(**params).execute()

    response: MoveFileResponse = {
        "id": result["id"],
        "name": result["name"],
        "parents": result.get("parents", []),
        "webViewLink": result.get("webViewLink", ""),
    }
    return response


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/drive.file"]))
async def download_file(
    context: Context,
    file_path_or_id: Annotated[
        str,
        "The file path like folder/subfolder/filename or the file ID "
        "of the file to download Folders NOT supported. If providing a path, "
        "it will be resolved within 'My Drive' by default.",
    ],
    shared_drive_id: Annotated[
        str | None,
        "If the file is in a shared drive and using a path, provide the shared drive ID. "
        "Not needed when using file IDs. Defaults to None (uses 'My Drive').",
    ] = None,
) -> Annotated[
    DownloadFileResponse,
    "For small files (<5MB): file content (base64 encoded) and metadata. "
    "For large files: metadata with requires_chunked_download=True and instructions.",
]:
    """Download a blob file (non-workspace file) from Google Drive as base64 encoded content.

    For small files (under ~5MB raw), returns the file content directly in the response as base64.
    For large files, returns metadata with requires_chunked_download=True - use download_file_chunk
    to retrieve the file in parts.

    By default, paths are resolved in My Drive. For shared drives, use file IDs or provide
    shared_drive_id."""
    service = build_drive_service(context.get_auth_token_or_empty())
    file_id = resolve_file_id(service, file_path_or_id, shared_drive_id)

    # Get file metadata
    file_metadata = service.files().get(fileId=file_id, fields="id, name, mimeType, size").execute()
    mime_type = file_metadata.get("mimeType", "")
    is_google_workspace_file = mime_type.startswith("application/vnd.google-apps.")

    if is_google_workspace_file:
        raise ToolExecutionError(
            message="Downloading Google Workspace files is not supported",
            developer_message=(
                f"File '{file_metadata['name']}' is a Google Workspace file "
                f"({mime_type}). This tool does not support downloading/exporting "
                "Google Workspace files."
            ),
        )

    file_size = int(file_metadata.get("size", 0))

    # For large binary files, return chunked download instructions
    if file_size > MAX_RESPONSE_CONTENT_BYTES:
        return {
            "id": file_metadata["id"],
            "name": file_metadata["name"],
            "mimeType": mime_type,
            "size": file_size,
            "requires_chunked_download": True,
            "total_size_bytes": file_size,
            "recommended_chunk_size": DEFAULT_CHUNK_SIZE_BYTES,
            "message": (
                "File is too large for direct download. "
                "Use download_file_chunk to retrieve the file in parts."
            ),
        }

    content = service.files().get_media(fileId=file_id).execute()

    content_encoded = encode_content(content) if isinstance(content, bytes) else content

    response: DownloadFileResponse = {
        "id": file_metadata["id"],
        "name": file_metadata["name"],
        "mimeType": mime_type,
        "size": file_size,
        "content": content_encoded,
    }
    return response


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/drive.file"]))
async def download_file_chunk(
    context: Context,
    file_path_or_id: Annotated[
        str,
        "The file path like folder/subfolder/filename or the file ID "
        "to download a chunk from. If providing a path, it will be resolved within "
        "'My Drive' by default.",
    ],
    start_byte: Annotated[
        int,
        "The starting byte position for this chunk (0-indexed).",
    ],
    chunk_size: Annotated[
        int,
        "The size of the chunk to download in bytes. Max 5MB (5242880). Defaults to 5MB (5242880).",
    ] = DEFAULT_CHUNK_SIZE_BYTES,
    shared_drive_id: Annotated[
        str | None,
        "If the file is in a shared drive and using a path, provide the shared drive ID. "
        "Not needed when using file IDs. Defaults to None (uses 'My Drive').",
    ] = None,
) -> Annotated[
    DownloadFileChunkResponse,
    "Chunk content (base64 encoded), byte range info, and progress details",
]:
    """Download a specific byte range of a file from Google Drive.

    Use this for large files that require chunked download (when download_file returns
    requires_chunked_download=True). Call repeatedly with increasing start_byte values
    to retrieve the complete file.

    Returns the chunk content as base64, along with progress information including
    whether this is the final chunk."""
    if chunk_size > MAX_CHUNK_SIZE_BYTES:
        raise RetryableToolError(
            message=(
                f"Chunk size {chunk_size} bytes exceeds maximum allowed "
                f"{MAX_CHUNK_SIZE_BYTES} bytes."
            ),
            additional_prompt_content=(
                f"Chunk size {chunk_size} bytes exceeds maximum allowed "
                f"({MAX_CHUNK_SIZE_BYTES} bytes). Please try a smaller chunk size."
            ),
        )
    token = context.get_auth_token_or_empty()
    service = build_drive_service(token)
    file_id = resolve_file_id(service, file_path_or_id, shared_drive_id)

    file_metadata = service.files().get(fileId=file_id, fields="id, name, mimeType, size").execute()
    mime_type = file_metadata.get("mimeType", "")
    is_google_workspace_file = mime_type.startswith("application/vnd.google-apps.")

    # Google Workspace files are not supported for download.
    if is_google_workspace_file:
        raise ToolExecutionError(
            message="Downloading Google Workspace files is not supported by this tool",
            developer_message=(
                "Google Workspace files (Docs, Sheets, Slides, Drawings) are not supported for "
                "download in this toolkit."
            ),
        )

    total_size = int(file_metadata.get("size", 0))
    if total_size == 0:
        raise ToolExecutionError(
            message="Cannot determine file size for chunked download",
            developer_message="File has no size metadata",
        )

    # Calculate actual chunk boundaries
    end_byte = min(start_byte + chunk_size - 1, total_size - 1)
    actual_chunk_size = end_byte - start_byte + 1

    download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    headers = {
        "Authorization": f"Bearer {token}",
        "Range": f"bytes={start_byte}-{end_byte}",
    }

    async with httpx.AsyncClient() as client:
        http_response = await client.get(download_url, headers=headers, timeout=UPLOAD_TIMEOUT)

        if http_response.status_code not in (200, 206):
            raise ToolExecutionError(
                message=f"Failed to download chunk: HTTP {http_response.status_code}",
                developer_message=f"Google API error: {http_response.text}",
            )

        chunk_content = http_response.content

    content_encoded = encode_content(chunk_content)

    # Calculate progress
    is_final_chunk = end_byte >= total_size - 1
    next_start_byte = end_byte + 1 if not is_final_chunk else None
    progress_percent = round((end_byte + 1) / total_size * 100, 1)

    chunk_response: DownloadFileChunkResponse = {
        "id": file_metadata["id"],
        "name": file_metadata["name"],
        "mimeType": mime_type,
        "chunk_start_byte": start_byte,
        "chunk_end_byte": end_byte,
        "chunk_size": actual_chunk_size,
        "total_size_bytes": total_size,
        "content": content_encoded,
        "is_final_chunk": is_final_chunk,
        "next_start_byte": next_start_byte,
        "progress_percent": progress_percent,
    }
    return chunk_response


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/drive.file"]))
async def upload_file(
    context: Context,
    file_name: Annotated[
        str,
        "The name for the uploaded file",
    ],
    source_url: Annotated[
        str,
        "The public download URL to fetch the file content from. "
        "The tool will download from this URL and upload to Google Drive",
    ],
    mime_type: Annotated[
        UploadMimeType | None,
        "The file type. If not provided, will be inferred from the URL or Content-Type header. "
        "Supported: text (txt, csv, json, html, md), pdf, images (png, jpeg, gif). "
        "Defaults to None (auto-detect).",
    ] = None,
    destination_folder_path_or_id: Annotated[
        str | None,
        "The folder path like folder/subfolder or folder ID where to upload. "
        "If None, uploads to the root of 'My Drive'. If providing a path, it will be "
        "resolved within 'My Drive' by default. Defaults to None.",
    ] = None,
    shared_drive_id: Annotated[
        str | None,
        "If uploading to a folder in a shared drive using a path, provide the shared drive ID. "
        "Not needed when using folder IDs or uploading to My Drive. Defaults to None ('My Drive')",
    ] = None,
) -> Annotated[
    UploadFileResponse,
    "Uploaded file information including ID, name, web view link, and location",
]:
    """Upload a file to Google Drive from a URL.

    Fetches the file content from the provided URL and uploads it to Google Drive.
    Supports files of any size - uses resumable upload internally for large files.

    CANNOT upload Google Workspace files (Google Docs, Sheets, Slides)
    CANNOT upload files larger than 25MB
    """
    token = context.get_auth_token_or_empty()
    service = build_drive_service(token)

    # Fetch content from URL
    content_bytes, content_type_header = await fetch_from_url(source_url)

    # Determine MIME type
    if mime_type is not None:
        actual_mime_type = mime_type.value
    else:
        # Try to infer from URL or Content-Type header
        inferred = infer_mime_type(source_url, content_type_header)
        if inferred is None:
            raise ToolExecutionError(
                message="Could not determine file type",
                developer_message=(
                    f"Unable to infer MIME type from URL '{source_url}' or "
                    f"Content-Type header '{content_type_header}'. "
                    "Please specify mime_type explicitly."
                ),
            )
        actual_mime_type = inferred

    folder_id = None
    if destination_folder_path_or_id:
        folder_id = resolve_file_id(
            service, destination_folder_path_or_id, shared_drive_id, require_folder=True
        )

    content_size = len(content_bytes)
    if content_size <= MAX_SIMPLE_UPLOAD_BYTES:
        # Simple upload for small files
        file_metadata: dict[str, Any] = {"name": file_name}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaIoBaseUpload(
            io.BytesIO(content_bytes),
            mimetype=actual_mime_type,
            resumable=False,
        )

        params: dict[str, Any] = {
            "body": file_metadata,
            "media_body": media,
            "fields": "id, name, mimeType, parents, webViewLink",
        }
        if shared_drive_id:
            params["supportsAllDrives"] = True

        result = service.files().create(**params).execute()

        upload_response: UploadFileResponse = {
            "id": result.get("id"),
            "name": result.get("name"),
            "mimeType": result.get("mimeType", actual_mime_type),
            "parents": result.get("parents", []),
            "webViewLink": result.get("webViewLink", ""),
        }
        return upload_response
    # Resumable upload for large files
    result = await upload_file_resumable(
        token=token,
        file_name=file_name,
        content=content_bytes,
        mime_type=actual_mime_type,
        destination_folder_id=folder_id,
    )

    return {
        "id": result["id"],
        "name": result["name"],
        "mimeType": result.get("mimeType", actual_mime_type),
        "parents": result.get("parents", []),
        "webViewLink": result.get("webViewLink", ""),
    }
