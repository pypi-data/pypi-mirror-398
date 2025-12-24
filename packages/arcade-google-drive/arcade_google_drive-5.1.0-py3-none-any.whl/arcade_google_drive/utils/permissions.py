from typing import Any, cast

from googleapiclient.discovery import Resource


def get_existing_permissions(  # type: ignore[no-any-unimported]
    service: Resource,
    file_id: str,
    shared_drive_id: str | None,
) -> dict[str, dict[str, Any]]:
    """Get existing permissions for a file, indexed by email address.

    Args:
        service: Google Drive API service
        file_id: The file ID to get permissions for
        shared_drive_id: If provided, supports shared drive files

    Returns:
        Dictionary mapping lowercase email addresses to permission objects
    """
    list_params: dict[str, Any] = {
        "fileId": file_id,
        "fields": "permissions(id, type, role, emailAddress)",
    }
    if shared_drive_id:
        list_params["supportsAllDrives"] = True

    existing_perms = service.permissions().list(**list_params).execute()
    return {
        p.get("emailAddress", "").lower(): p
        for p in existing_perms.get("permissions", [])
        if p.get("emailAddress")
    }


def update_permission(  # type: ignore[no-any-unimported]
    service: Resource,
    file_id: str,
    permission_id: str,
    role: str,
    shared_drive_id: str | None,
) -> dict[str, Any]:
    """Update an existing permission's role.

    Args:
        service: Google Drive API service
        file_id: The file ID
        permission_id: The permission ID to update
        role: The new role value
        shared_drive_id: If provided, supports shared drive files

    Returns:
        Updated permission object
    """
    update_params: dict[str, Any] = {
        "fileId": file_id,
        "permissionId": permission_id,
        "body": {"role": role},
        "fields": "id, type, role, emailAddress",
    }
    if shared_drive_id:
        update_params["supportsAllDrives"] = True

    return cast(dict[str, Any], service.permissions().update(**update_params).execute())


def create_permission(  # type: ignore[no-any-unimported]
    service: Resource,
    file_id: str,
    email: str,
    role: str,
    send_notification_email: bool,
    message: str | None,
    shared_drive_id: str | None,
) -> dict[str, Any]:
    """Create a new permission for a user.

    Args:
        service: Google Drive API service
        file_id: The file ID
        email: Email address of the user to share with
        role: The permission role
        send_notification_email: Whether to send notification
        message: Optional message for the notification email
        shared_drive_id: If provided, supports shared drive files

    Returns:
        Created permission object
    """
    permission_body = {
        "type": "user",
        "role": role,
        "emailAddress": email,
    }

    create_params: dict[str, Any] = {
        "fileId": file_id,
        "body": permission_body,
        "sendNotificationEmail": send_notification_email,
        "fields": "id, type, role, emailAddress",
    }

    if message:
        create_params["emailMessage"] = message

    if shared_drive_id:
        create_params["supportsAllDrives"] = True

    return cast(dict[str, Any], service.permissions().create(**create_params).execute())
