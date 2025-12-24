import json
from typing import Any

import httpx
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_google_drive.constants import (
    RESUMABLE_CHUNK_SIZE,
    RESUMABLE_UPLOAD_URL,
    UPLOAD_TIMEOUT,
)


async def initiate_resumable_upload_session(
    token: str,
    file_name: str,
    mime_type: str,
    total_size_bytes: int,
    destination_folder_id: str | None,
) -> str:
    """Initiate a resumable upload session with Google Drive.

    Args:
        token: OAuth2 access token
        file_name: Name for the uploaded file
        mime_type: MIME type of the file
        total_size_bytes: Total file size
        destination_folder_id: Optional folder ID to upload into

    Returns:
        Session URI for uploading chunks

    Raises:
        ToolExecutionError: If session initiation fails
    """
    file_metadata: dict[str, Any] = {"name": file_name}
    if destination_folder_id:
        file_metadata["parents"] = [destination_folder_id]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Upload-Content-Type": mime_type,
        "X-Upload-Content-Length": str(total_size_bytes),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            RESUMABLE_UPLOAD_URL,
            headers=headers,
            content=json.dumps(file_metadata),
        )
        response.raise_for_status()

        session_uri = response.headers.get("Location")
        if not session_uri:
            raise ToolExecutionError(
                message="Failed to get upload session URI",
                developer_message="Response missing Location header",
            )

        return str(session_uri)


async def upload_chunk_to_session(
    session_uri: str,
    chunk_bytes: bytes,
    start_byte: int,
    total_size_bytes: int,
) -> dict[str, Any]:
    """Upload a chunk of data to an active upload session.

    Args:
        session_uri: The upload session URI
        chunk_bytes: The chunk data as bytes
        start_byte: Starting byte position (0-indexed)
        total_size_bytes: Total file size

    Returns:
        Progress dict if more chunks needed, or completed file info with status="complete"

    Raises:
        ToolExecutionError: If upload fails
    """
    chunk_size = len(chunk_bytes)
    end_byte = start_byte + chunk_size - 1

    headers = {
        "Content-Length": str(chunk_size),
        "Content-Range": f"bytes {start_byte}-{end_byte}/{total_size_bytes}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(
            session_uri,
            headers=headers,
            content=chunk_bytes,
            timeout=UPLOAD_TIMEOUT,
        )

        # 308 = Resume Incomplete (more chunks needed)
        if response.status_code == 308:
            return {
                "status": "in_progress",
                "bytes_uploaded": end_byte + 1,
                "total_size_bytes": total_size_bytes,
                "progress_percent": round((end_byte + 1) / total_size_bytes * 100, 1),
                "next_start_byte": end_byte + 1,
            }
        # 200/201 = Upload complete
        elif response.status_code in (200, 201):
            result = response.json()
            return {
                "status": "complete",
                "id": result.get("id"),
                "name": result.get("name"),
                "mimeType": result.get("mimeType"),
                "parents": result.get("parents", []),
                "webViewLink": result.get("webViewLink", ""),
            }
        else:
            raise ToolExecutionError(
                message=f"Chunk upload failed: {response.status_code}",
                developer_message=f"Google API error: {response.text}",
            )


async def upload_file_resumable(
    token: str,
    file_name: str,
    content: bytes,
    mime_type: str,
    destination_folder_id: str | None,
) -> dict[str, Any]:
    """Upload a file using resumable upload (for files > 5MB).

    Handles the entire resumable upload process internally:
    1. Initiates upload session
    2. Uploads content in chunks
    3. Returns completed file info

    Args:
        token: OAuth2 access token
        file_name: Name for the uploaded file
        content: File content as bytes
        mime_type: MIME type of the file
        destination_folder_id: Optional folder ID to upload into

    Returns:
        Completed file info dict

    Raises:
        ToolExecutionError: If upload fails
    """
    total_size = len(content)

    # Initiate the upload session
    session_uri = await initiate_resumable_upload_session(
        token=token,
        file_name=file_name,
        mime_type=mime_type,
        total_size_bytes=total_size,
        destination_folder_id=destination_folder_id,
    )

    start_byte = 0
    result: dict[str, Any] = {}
    while start_byte < total_size:
        # Calculate chunk size (align to 256KB except for last chunk)
        remaining = total_size - start_byte
        chunk_size = RESUMABLE_CHUNK_SIZE if remaining > RESUMABLE_CHUNK_SIZE else remaining

        chunk = content[start_byte : start_byte + chunk_size]

        result = await upload_chunk_to_session(
            session_uri=session_uri,
            chunk_bytes=chunk,
            start_byte=start_byte,
            total_size_bytes=total_size,
        )

        if result.get("status") == "complete":
            return result

        start_byte = result.get("next_start_byte", start_byte + chunk_size)

    # Should not reach here
    return {}
