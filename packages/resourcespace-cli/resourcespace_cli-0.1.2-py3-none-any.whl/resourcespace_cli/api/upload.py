"""Upload API functions for ResourceSpace CLI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from resourcespace_cli.client import ResourceSpaceClient


def create_resource(
    client: ResourceSpaceClient,
    resource_type: int,
    *,
    archive: int = 0,
) -> int:
    """Create a new empty resource.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_type: The resource type ID.
        archive: Archive state (0 = active, default).

    Returns:
        The new resource ID.
    """
    result: int = client.call(
        "create_resource",
        resource_type=resource_type,
        archive=archive,
    )
    return result


def upload_file(
    client: ResourceSpaceClient,
    resource_id: int,
    filepath: Path,
    *,
    no_exif: bool = False,
) -> bool:
    """Upload a file to an existing resource.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_id: The resource ID to upload to.
        filepath: Path to the file to upload.
        no_exif: If True, do not extract EXIF data.

    Returns:
        True if upload succeeded.
    """
    return client.upload_file(resource_id, filepath, no_exif=no_exif)


def update_field(
    client: ResourceSpaceClient,
    resource_id: int,
    field_id: int,
    value: str,
) -> bool:
    """Update a metadata field on a resource.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_id: The resource ID.
        field_id: The field ID to update.
        value: The new field value.

    Returns:
        True if update succeeded.
    """
    result: bool = client.call(
        "update_field",
        resource=resource_id,
        field=field_id,
        value=value,
    )
    return result


def add_resource_to_collection(
    client: ResourceSpaceClient,
    resource_id: int,
    collection_id: int,
) -> bool:
    """Add a resource to a collection.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_id: The resource ID to add.
        collection_id: The collection ID.

    Returns:
        True if successful.
    """
    result: bool = client.call(
        "add_resource_to_collection",
        resource=resource_id,
        collection=collection_id,
    )
    return result


def get_resource_type_fields(
    client: ResourceSpaceClient,
    resource_type: int,
) -> list[dict[str, Any]]:
    """Get all metadata fields for a resource type.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_type: The resource type ID.

    Returns:
        List of field dictionaries with ref, name, title, etc.
    """
    result: list[dict[str, Any]] = client.call(
        "get_resource_type_fields",
        resource_type=resource_type,
    )
    return result
