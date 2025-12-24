from typing import Annotated

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google

from arcade_google_drive.enums import Corpora, OrderBy
from arcade_google_drive.models import GoogleDriveFileType, SearchMetadata
from arcade_google_drive.tool_responses import SearchFilesResponse
from arcade_google_drive.utils.drive_client import build_drive_service
from arcade_google_drive.utils.resolution import resolve_file_id
from arcade_google_drive.utils.search_query import SearchQueryBuilder


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    ),
)
async def search_files(
    context: Context,
    query: Annotated[
        str,
        "The exact search query to send to the Google Drive API to find files in Google Drive. "
        "The tool will construct the query for you. "
        "Will search for filenames and file contents that match the provided query.",
    ],
    folder_path_or_id: Annotated[
        str | None,
        "Search only within this specific folder. "
        "Provide either a path like folder/subfolder or a folder ID. "
        "If None, searches across all accessible locations. Defaults to None.",
    ] = None,
    shared_drive_id: Annotated[
        str | None,
        "If provided, search only within this shared drive. "
        "Defaults to None (searches My Drive and optionally all shared drives).",
    ] = None,
    include_shared_drives: Annotated[
        bool,
        "If True and shared_drive_id is not set, include all shared drives in search. "
        "Defaults to False (My Drive only).",
    ] = False,
    include_organization_domain_documents: Annotated[
        bool,
        "Whether to include documents from the organization's domain. "
        "This is applicable to admin users who have permissions to view "
        "organization-wide documents in a Google Workspace account. "
        "Defaults to False.",
    ] = False,
    order_by: Annotated[
        list[OrderBy] | None,
        "Sort order for search results. "
        "Defaults to listing the most recently modified documents first. "
        "If the query contains 'fullText', then the order_by will be ignored.",
    ] = None,
    limit: Annotated[
        int | None,
        "The maximum number of search results to return. Defaults to 50.",
    ] = 50,
    file_types: Annotated[
        list[GoogleDriveFileType] | None,
        "Filter by specific file types. Defaults to None, which includes all file types.",
    ] = None,
) -> Annotated[
    SearchFilesResponse,
    "Search results containing matching files from Google Drive with metadata and file information",
]:
    """
    Search for files in Google Drive.

    The provided 'query' should only contain the search terms.
    The tool will construct the full search query for you.
    """
    service = build_drive_service(context.get_auth_token_or_empty())

    folder_id = None
    if folder_path_or_id:
        folder_id = resolve_file_id(
            service, folder_path_or_id, shared_drive_id, require_folder=True
        )

    # Build search query
    search_query = SearchQueryBuilder.build_search_query(query, file_types, folder_id)

    # Build request parameters
    fields = (
        "files(id, name, mimeType, size, createdTime, modifiedTime, "
        "owners, parents, driveId, webViewLink, thumbnailLink)"
    )
    params = {
        "q": search_query,
        "pageSize": limit,
        "fields": fields,
    }

    # Add ordering
    if "fullText" in search_query:
        # Google drive API does not support other order_by values for
        # queries with fullText search.
        order_by = None
    elif order_by:
        params["orderBy"] = ",".join([item.value for item in order_by])
    else:
        params["orderBy"] = OrderBy.MODIFIED_TIME_DESC.value

    # Add drive-specific parameters
    if shared_drive_id or include_shared_drives or include_organization_domain_documents:
        params["includeItemsFromAllDrives"] = "true"
        params["supportsAllDrives"] = "true"

    if shared_drive_id:
        params["driveId"] = shared_drive_id
        params["corpora"] = Corpora.DRIVE.value

    # Execute search
    results = service.files().list(**params).execute()
    files = results.get("files", [])

    order_by_str = params.get("orderBy")
    if not isinstance(order_by_str, str):
        order_by_str = None

    search_metadata: SearchMetadata = {
        "file_types_filtered": file_types,
        "include_shared_drives": include_shared_drives,
        "order_by": order_by_str,
    }

    response: SearchFilesResponse = {
        "query": query,
        "search_query": search_query,
        "total_results": len(files),
        "files": files,
        "search_metadata": search_metadata,
    }

    return response
