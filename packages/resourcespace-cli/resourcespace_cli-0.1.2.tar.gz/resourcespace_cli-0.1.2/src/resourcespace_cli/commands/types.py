"""Resource types commands for ResourceSpace CLI."""

from __future__ import annotations

import json
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from resourcespace_cli.api.types import get_resource_types
from resourcespace_cli.client import ResourceSpaceClient
from resourcespace_cli.config import load_config
from resourcespace_cli.output import get_console
from resourcespace_cli.utils.errors import handle_exception


@click.group()
def types() -> None:
    """Manage ResourceSpace resource types."""


@types.command("list")
@click.pass_context
def types_list(ctx: click.Context) -> None:
    """List all available resource types.

    Displays resource type ID and name for each configured type.

    \b
    Examples:
        rs types list
        rs --json types list
    """
    json_output: bool = ctx.obj.get("json_output", False)

    try:
        config = load_config()

        with ResourceSpaceClient(config) as client:
            types_data = get_resource_types(client)

        if json_output:
            click.echo(
                json.dumps(
                    {
                        "status": "success",
                        "resource_types": types_data,
                        "count": len(types_data),
                    },
                    indent=2,
                )
            )
        else:
            console = get_console(ctx)
            _print_types_table(console, types_data)

    except Exception as e:
        handle_exception(ctx, e)


def _print_types_table(console: Console, types_data: list[dict[str, Any]]) -> None:
    """Print resource types as a Rich table.

    Args:
        console: Rich Console instance.
        types_data: List of resource type dictionaries from the API.
    """
    if not types_data:
        console.print("[dim]No resource types found.[/dim]")
        return

    table = Table(title="Resource Types")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")

    for resource_type in types_data:
        type_id = str(resource_type.get("ref", resource_type.get("id", "?")))
        name = resource_type.get("name", "Unnamed")

        table.add_row(type_id, name)

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Total: {len(types_data)} resource type(s)[/dim]")
