"""Resource API functions for ResourceSpace CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from resourcespace_cli.client import ResourceSpaceClient


def get_resource_data(client: ResourceSpaceClient, resource_id: int) -> dict[str, Any]:
    """Get metadata for a single resource.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_id: The resource ID to fetch.

    Returns:
        Resource dictionary with metadata fields.
    """
    result: dict[str, Any] = client.call("get_resource_data", resource=resource_id)
    return result


def get_resource_path(
    client: ResourceSpaceClient,
    resource_id: int,
    *,
    size: str = "",
) -> str:
    """Get the download path/URL for a resource.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_id: The resource ID.
        size: Size variant (empty for original).

    Returns:
        Download URL for the resource.
    """
    result: str = client.call("get_resource_path", resource=resource_id, size=size)
    return result


def get_resource_field_data(
    client: ResourceSpaceClient,
    resource_id: int,
) -> list[dict[str, Any]]:
    """Get full metadata fields for a resource.

    Unlike get_resource_data which returns truncated summaries,
    this returns complete field-level metadata.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_id: The resource ID to fetch.

    Returns:
        List of field dictionaries with ref, name, value, etc.
    """
    result: list[dict[str, Any]] = client.call(
        "get_resource_field_data", resource=resource_id
    )
    return result


def get_resource_all_image_sizes(
    client: ResourceSpaceClient,
    resource_id: int,
) -> list[dict[str, Any]]:
    """Get all available image sizes for a resource.

    For multi-page resources, includes sizes for each page.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_id: The resource ID.

    Returns:
        List of size dictionaries with id, name, width, height, etc.
    """
    result: list[dict[str, Any]] = client.call(
        "get_resource_all_image_sizes", resource=resource_id
    )
    return result


def get_alternative_files(
    client: ResourceSpaceClient,
    resource_id: int,
) -> list[dict[str, Any]]:
    """Get alternative files for a resource.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_id: The resource ID.

    Returns:
        List of alternative file dictionaries with ref, name, file_extension, file_size.
    """
    result: list[dict[str, Any]] = client.call(
        "get_alternative_files", resource=resource_id
    )
    return result


def get_collection(
    client: ResourceSpaceClient,
    collection_id: int,
) -> dict[str, Any]:
    """Get details for a specific collection.

    Args:
        client: An authenticated ResourceSpace API client.
        collection_id: The collection ID.

    Returns:
        Collection dictionary with name, description, owner, etc.
    """
    result: dict[str, Any] = client.call("get_collection", ref=collection_id)
    return result


def get_resource_collections(
    client: ResourceSpaceClient,
    resource_id: int,
) -> list[dict[str, Any]]:
    """Get all collections containing a specific resource.

    Note: ResourceSpace API does not have a direct endpoint for this.
    This function searches through user collections to find membership.

    Args:
        client: An authenticated ResourceSpace API client.
        resource_id: The resource ID to find.

    Returns:
        List of collection dictionaries that contain this resource.
    """
    from resourcespace_cli.api.search import do_search

    user_collections = client.get_user_collections()
    containing_collections: list[dict[str, Any]] = []

    for collection in user_collections:
        coll_id = collection.get("ref", collection.get("id"))
        if coll_id:
            # Search within this collection for the resource
            results = do_search(client, f"!collection{coll_id}", limit=9999)
            resource_ids = [r.get("ref", r.get("id")) for r in results]
            if resource_id in [int(rid) for rid in resource_ids if rid]:
                # Get full collection details
                try:
                    full_collection = get_collection(client, int(coll_id))
                    containing_collections.append(full_collection)
                except Exception:
                    # If get_collection fails (permissions), use basic info
                    containing_collections.append(collection)

    return containing_collections
