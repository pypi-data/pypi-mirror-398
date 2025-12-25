"""Resource types API functions for ResourceSpace CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from resourcespace_cli.client import ResourceSpaceClient


def get_resource_types(client: ResourceSpaceClient) -> list[dict[str, Any]]:
    """Fetch all resource types from ResourceSpace.

    Args:
        client: An authenticated ResourceSpace API client.

    Returns:
        A list of resource type dictionaries containing type information.
    """
    result: list[dict[str, Any]] = client.call("get_resource_types")
    return result
