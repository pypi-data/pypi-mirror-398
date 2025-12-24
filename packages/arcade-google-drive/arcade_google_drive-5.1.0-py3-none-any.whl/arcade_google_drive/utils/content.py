import base64
import mimetypes
from urllib.parse import urlparse

import httpx
from arcade_mcp_server.exceptions import ToolExecutionError

from arcade_google_drive.constants import (
    DEFAULT_USER_AGENT,
    EXTENSION_TO_MIME_TYPE,
    MAX_URL_UPLOAD_SIZE_BYTES,
    URL_FETCH_TIMEOUT,
)


def _format_size_mb(size_bytes: int) -> str:
    """Format bytes as MB with 1 decimal place."""
    return f"{size_bytes / (1024 * 1024):.1f}MB"


async def fetch_from_url(url: str, timeout: float = URL_FETCH_TIMEOUT) -> tuple[bytes, str | None]:
    """Fetch content from a URL.

    Args:
        url: The URL to fetch content from
        timeout: Request timeout in seconds

    Returns:
        Tuple of (content_bytes, content_type) where content_type is the
        Content-Type header value (may be None if not provided)

    Raises:
        ToolExecutionError: If the URL cannot be fetched or file is too large
    """
    max_size_mb = _format_size_mb(MAX_URL_UPLOAD_SIZE_BYTES)

    # Validate URL scheme
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ToolExecutionError(
            message=f"Invalid URL scheme: {parsed.scheme}",
            developer_message="Only http:// and https:// URLs are supported",
        )

    # Use browser-like headers to avoid being blocked by websites
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "*/*",
    }

    client = httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers)
    async with client, client.stream("GET", url) as response:
        response.raise_for_status()

        # Check Content-Length header if available so we can enforce a size limit
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_URL_UPLOAD_SIZE_BYTES:
                    raise ToolExecutionError(
                        message=(
                            f"File too large: {_format_size_mb(size)}. "
                            f"Maximum allowed size is {max_size_mb}"
                        ),
                        developer_message=(
                            f"The file at '{url}' is {size} bytes, which exceeds "
                            f"the maximum upload size of {MAX_URL_UPLOAD_SIZE_BYTES} "
                            f"bytes ({max_size_mb})"
                        ),
                    )
            except ValueError:
                pass  # Invalid Content-Length header, proceed with download

        # Stream the download with size limit enforcement
        chunks = []
        total_size = 0
        async for chunk in response.aiter_bytes():
            total_size += len(chunk)
            if total_size > MAX_URL_UPLOAD_SIZE_BYTES:
                raise ToolExecutionError(
                    message=f"File too large. Maximum allowed size is {max_size_mb}",
                    developer_message=(
                        f"The file at '{url}' exceeds the maximum upload size "
                        f"of {MAX_URL_UPLOAD_SIZE_BYTES} bytes ({max_size_mb}). "
                        "Download aborted after receiving more than the allowed limit."
                    ),
                )
            chunks.append(chunk)

        content_type = response.headers.get("content-type")
        # Extract just the MIME type
        if content_type and ";" in content_type:
            content_type = content_type.split(";")[0].strip()

        return b"".join(chunks), content_type


def infer_mime_type(url: str, content_type: str | None) -> str | None:
    """Infer MIME type from URL and/or Content-Type header.

    Priority:
    1. Content-Type header (if provided and valid)
    2. File extension from URL
    3. None (caller should handle)

    Args:
        url: The URL the content was fetched from
        content_type: The Content-Type header value (if available)

    Returns:
        Inferred MIME type or None if cannot be determined
    """
    if content_type and "/" in content_type:
        return content_type

    parsed = urlparse(url)
    path = parsed.path.lower()

    for ext, mime in EXTENSION_TO_MIME_TYPE.items():
        if path.endswith(ext):
            return mime

    guessed_type, _ = mimetypes.guess_type(url)
    if guessed_type:
        return guessed_type

    return None


def encode_content(content: bytes) -> str:
    """Encode binary content to base64 string.

    Args:
        content: Binary content to encode

    Returns:
        Base64-encoded string
    """
    return base64.b64encode(content).decode("utf-8")
