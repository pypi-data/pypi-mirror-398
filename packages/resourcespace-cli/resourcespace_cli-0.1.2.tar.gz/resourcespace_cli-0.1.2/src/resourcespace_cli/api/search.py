"""Search API functions for ResourceSpace CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from resourcespace_cli.client import ResourceSpaceClient


def do_search(
    client: ResourceSpaceClient,
    search_query: str,
    *,
    resource_type: int | None = None,
    collection: int | None = None,
    offset: int = 0,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search for resources in ResourceSpace.

    Args:
        client: An authenticated ResourceSpace API client.
        search_query: The search query string.
        resource_type: Optional resource type ID to filter by.
        collection: Optional collection ID to filter by.
        offset: Number of results to skip (for pagination).
        limit: Maximum number of results to return.

    Returns:
        A list of resource dictionaries matching the search criteria.
    """
    params: dict[str, Any] = {
        "search": search_query,
        "fetchrows": limit,
        "offset": offset,
    }

    if resource_type is not None:
        params["restypes"] = str(resource_type)

    if collection is not None:
        params["archive"] = collection

    result: list[dict[str, Any]] = client.call("do_search", **params)
    return result
