"""Search command for ResourceSpace CLI."""

from __future__ import annotations

import json
from typing import Any

import click
from rich.table import Table

from resourcespace_cli.api.search import do_search
from resourcespace_cli.client import ResourceSpaceClient
from resourcespace_cli.config import load_config
from resourcespace_cli.output import get_console
from resourcespace_cli.utils.errors import handle_exception
from resourcespace_cli.utils.validation import validate_search_query


@click.command()
@click.argument("query")
@click.option(
    "--type",
    "resource_type",
    type=int,
    default=None,
    help="Filter by resource type ID.",
)
@click.option(
    "--collection",
    type=int,
    default=None,
    help="Filter by collection ID.",
)
@click.option(
    "--page",
    type=int,
    default=1,
    help="Page number (default: 1).",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Results per page (default: 20).",
)
@click.pass_context
def search(
    ctx: click.Context,
    query: str,
    resource_type: int | None,
    collection: int | None,
    page: int,
    limit: int,
) -> None:
    """Search for resources in ResourceSpace.

    Searches the ResourceSpace system using the provided QUERY string.
    Results can be filtered by resource type and collection.

    \b
    Examples:
        rs search "landscape"
        rs search "photo" --type 1
        rs search "document" --collection 5 --limit 50
        rs --json search "image" --page 2
    """
    json_output: bool = ctx.obj.get("json_output", False)

    try:
        # Validate input before making API calls
        validated = validate_search_query(
            query=query,
            page=page,
            limit=limit,
            resource_type=resource_type,
            collection_id=collection,
        )

        # Calculate offset from page number
        offset = (validated.page - 1) * validated.limit

        config = load_config()

        with ResourceSpaceClient(config) as client:
            results = do_search(
                client,
                validated.query,
                resource_type=validated.resource_type,
                collection=validated.collection_id,
                offset=offset,
                limit=validated.limit,
            )

        if json_output:
            click.echo(
                json.dumps(
                    {
                        "status": "success",
                        "query": validated.query,
                        "results": results,
                        "count": len(results),
                        "page": validated.page,
                        "limit": validated.limit,
                    },
                    indent=2,
                )
            )
        else:
            _print_search_results(ctx, results, validated.query, validated.page, validated.limit)

    except Exception as e:
        handle_exception(ctx, e)


def _print_search_results(
    ctx: click.Context,
    results: list[dict[str, Any]],
    query: str,
    page: int,
    limit: int,
) -> None:
    """Print search results as a Rich table.

    Args:
        ctx: Click context.
        results: List of resource dictionaries from the API.
        query: The search query that was used.
        page: Current page number.
        limit: Results per page.
    """
    console = get_console(ctx)

    if not results:
        console.print(f"[dim]No results found for '{query}'.[/dim]")
        return

    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="green")
    table.add_column("Preview URL", style="blue")

    for resource in results:
        resource_id = str(resource.get("ref", resource.get("id", "?")))
        title = resource.get("field8", resource.get("title", "Untitled"))
        preview_url = _build_preview_url(resource)

        table.add_row(resource_id, title, preview_url)

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Page {page} | Showing {len(results)} result(s) (limit: {limit})[/dim]")


def _build_preview_url(resource: dict[str, Any]) -> str:
    """Build a preview URL for a resource.

    Args:
        resource: Resource dictionary from the API.

    Returns:
        Preview URL string or placeholder if not available.
    """
    preview_url = resource.get("preview", resource.get("url_pre", ""))

    if preview_url:
        return str(preview_url)

    return "[dim]N/A[/dim]"
