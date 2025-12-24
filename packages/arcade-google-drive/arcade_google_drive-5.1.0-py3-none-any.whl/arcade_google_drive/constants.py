# Maximum file size for simple upload (limit set by the Google Drive API (5MB))
MAX_SIMPLE_UPLOAD_BYTES = 5 * 1024 * 1024

# Maximum raw content size before base64 encoding exceeds 10MB response limit
# Set to 5MB raw, which is ~6.7MB base64. Well below Engine's 10MB response limit.
MAX_RESPONSE_CONTENT_BYTES = 5 * 1024 * 1024

# Default chunk size for chunked downloads (5MB)
DEFAULT_CHUNK_SIZE_BYTES = 5 * 1024 * 1024

# Maximum chunk size for chunked downloads (limit set by the Google Drive API (5MB))
MAX_CHUNK_SIZE_BYTES = 5 * 1024 * 1024

# Chunk size for resumable uploads (5MB - must be multiple of 256KB)
RESUMABLE_CHUNK_SIZE = 5 * 1024 * 1024

# Google Drive API resumable upload endpoint
# Include fields parameter to get webViewLink in the response
RESUMABLE_UPLOAD_URL = (
    "https://www.googleapis.com/upload/drive/v3/files"
    "?uploadType=resumable"
    "&fields=id,name,mimeType,parents,webViewLink"
)

# Chunk alignment requirement (256KB)
CHUNK_ALIGNMENT = 256 * 1024

# Upload timeout (30 seconds for large chunks)
UPLOAD_TIMEOUT = 30.0

# Default timeout for URL fetching (in seconds)
URL_FETCH_TIMEOUT = 20.0

# Maximum file size for URL-based uploads (25MB)
# Files larger than this will be rejected to prevent OOM issues
MAX_URL_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024

# User-Agent header to use for URL fetching
# Many websites block requests without a proper User-Agent
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; ArcadeGoogleDrive/1.0; +https://arcade.dev)"

# Common MIME type mappings for file extensions
EXTENSION_TO_MIME_TYPE: dict[str, str] = {
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".json": "application/json",
    ".html": "text/html",
    ".htm": "text/html",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}
