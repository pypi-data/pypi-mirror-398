from typing import Annotated, cast

from arcade_mcp_server import Context, tool
from arcade_mcp_server.auth import Google

from arcade_google_drive.enums import PermissionRole
from arcade_google_drive.tool_responses import ShareFileResponse, SharePermission
from arcade_google_drive.utils.drive_client import build_drive_service
from arcade_google_drive.utils.permissions import (
    create_permission,
    get_existing_permissions,
    update_permission,
)
from arcade_google_drive.utils.resolution import resolve_file_id


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/drive.file"]))
async def share_file(
    context: Context,
    file_path_or_id: Annotated[
        str,
        "The file path like folder/subfolder/filename or the file ID to share. "
        "If providing a path, it will be resolved within My Drive by default.",
    ],
    email_addresses: Annotated[
        list[str],
        "List of email addresses like user@domain.com to share with",
    ],
    role: Annotated[
        PermissionRole,
        "The permission role to grant. Defaults to reader (view-only).",
    ] = PermissionRole.READER,
    send_notification_email: Annotated[
        bool,
        "Whether to send an email notification to the recipients. Defaults to True.",
    ] = True,
    message: Annotated[
        str | None,
        "Optional message to include in the notification email. Defaults to None.",
    ] = None,
    shared_drive_id: Annotated[
        str | None,
        "If the file is in a shared drive and using a path, provide the shared drive ID. "
        "Not needed when using file IDs. Defaults to None (uses My Drive).",
    ] = None,
) -> Annotated[
    ShareFileResponse,
    "Sharing confirmation with list of granted permissions including recipient emails and roles",
]:
    """Share a file or folder in Google Drive with specific people by granting them permissions.

    If a user already has permission on the file, their role will be updated to the new role.
    By default, paths are resolved in My Drive. For shared drives, use file IDs or provide
    shared_drive_id."""
    service = build_drive_service(context.get_auth_token_or_empty())

    # Resolve file ID
    file_id = resolve_file_id(service, file_path_or_id, shared_drive_id)

    # Get existing permissions
    existing_by_email = get_existing_permissions(service, file_id, shared_drive_id)

    # Create or update permissions for each email
    permissions: list[SharePermission] = []
    for email in email_addresses:
        email_lower = email.lower()
        existing = existing_by_email.get(email_lower)

        if existing:
            # User already has permission - update their role
            result = update_permission(
                service, file_id, existing["id"], role.value, shared_drive_id
            )
        else:
            # New user - create permission
            result = create_permission(
                service,
                file_id,
                email,
                role.value,
                send_notification_email,
                message,
                shared_drive_id,
            )

        permissions.append(
            cast(
                SharePermission,
                {
                    "id": result["id"],
                    "type": result["type"],
                    "role": result["role"],
                    "emailAddress": result.get("emailAddress", email),
                },
            )
        )

    response: ShareFileResponse = {
        "fileId": file_id,
        "permissions": permissions,
    }
    return response
