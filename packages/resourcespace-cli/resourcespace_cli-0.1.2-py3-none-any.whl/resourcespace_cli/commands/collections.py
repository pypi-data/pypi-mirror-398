"""Collections commands for ResourceSpace CLI."""

from __future__ import annotations

import json
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from resourcespace_cli.client import ResourceSpaceClient
from resourcespace_cli.config import load_config
from resourcespace_cli.output import get_console
from resourcespace_cli.utils.errors import handle_exception


@click.group()
def collections() -> None:
    """Manage ResourceSpace collections."""


@collections.command("list")
@click.pass_context
def collections_list(ctx: click.Context) -> None:
    """List all available collections.

    Displays collection ID, name, and resource count for each collection.

    \b
    Examples:
        rs collections list
        rs --json collections list
    """
    json_output: bool = ctx.obj.get("json_output", False)

    try:
        config = load_config()

        with ResourceSpaceClient(config) as client:
            collections_data = client.get_user_collections()

        if json_output:
            click.echo(
                json.dumps(
                    {
                        "status": "success",
                        "collections": collections_data,
                        "count": len(collections_data),
                    },
                    indent=2,
                )
            )
        else:
            console = get_console(ctx)
            _print_collections_table(console, collections_data)

    except Exception as e:
        handle_exception(ctx, e)


def _print_collections_table(console: Console, collections_data: list[dict[str, Any]]) -> None:
    """Print collections as a Rich table.

    Args:
        console: Rich Console instance.
        collections_data: List of collection dictionaries from the API.
    """
    if not collections_data:
        console.print("[dim]No collections found.[/dim]")
        return

    table = Table(title="Collections")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Resources", style="yellow", justify="right")

    for collection in collections_data:
        coll_id = str(collection.get("ref", collection.get("id", "?")))
        name = collection.get("name", "Unnamed")
        count = str(collection.get("count", collection.get("resource_count", "?")))

        table.add_row(coll_id, name, count)

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Total: {len(collections_data)} collection(s)[/dim]")
