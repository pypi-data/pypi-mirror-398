"""Info command for ResourceSpace CLI."""

from __future__ import annotations

import json
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from resourcespace_cli.api.resources import (
    get_alternative_files,
    get_resource_all_image_sizes,
    get_resource_collections,
    get_resource_data,
    get_resource_field_data,
    get_resource_path,
)
from resourcespace_cli.client import ResourceSpaceClient
from resourcespace_cli.config import load_config
from resourcespace_cli.exceptions import APIError
from resourcespace_cli.output import get_console, print_error
from resourcespace_cli.utils.errors import handle_exception
from resourcespace_cli.utils.validation import validate_resource_id


@click.command()
@click.argument("resource_id", type=int)
@click.pass_context
def info(ctx: click.Context, resource_id: int) -> None:
    """Display detailed information about a resource.

    Shows comprehensive resource details including all metadata fields,
    available file sizes/formats, collection membership, and preview URL.

    \b
    Examples:
        rs info 12345
        rs --json info 12345
    """
    json_output: bool = ctx.obj.get("json_output", False)

    try:
        # Validate input
        validated_id = validate_resource_id(resource_id)

        config = load_config()

        with ResourceSpaceClient(config) as client:
            # Fetch basic resource data
            resource_data = get_resource_data(client, validated_id)

            if not resource_data:
                print_error(ctx, f"Resource {validated_id} not found")
                return

            # Fetch field data for full metadata
            try:
                field_data = get_resource_field_data(client, validated_id)
            except APIError:
                field_data = []

            # Fetch available sizes
            try:
                sizes = get_resource_all_image_sizes(client, validated_id)
            except APIError:
                sizes = []

            # Fetch alternative files
            try:
                alternatives = get_alternative_files(client, validated_id)
            except APIError:
                alternatives = []

            # Fetch collections containing this resource
            try:
                collections = get_resource_collections(client, validated_id)
            except APIError:
                collections = []

            # Get preview URL
            try:
                preview_url = get_resource_path(client, validated_id, size="pre")
            except APIError:
                preview_url = ""

        if json_output:
            _output_json(
                validated_id,
                resource_data,
                field_data,
                sizes,
                alternatives,
                collections,
                preview_url,
            )
        else:
            console = get_console(ctx)
            _print_resource_info(
                console,
                validated_id,
                resource_data,
                field_data,
                sizes,
                alternatives,
                collections,
                preview_url,
            )

    except Exception as e:
        handle_exception(ctx, e)


def _output_json(
    resource_id: int,
    resource_data: dict[str, Any],
    field_data: list[dict[str, Any]],
    sizes: list[dict[str, Any]],
    alternatives: list[dict[str, Any]],
    collections: list[dict[str, Any]],
    preview_url: str,
) -> None:
    """Output resource information as JSON."""
    output = {
        "status": "success",
        "resource": {
            "id": resource_id,
            "data": resource_data,
            "preview_url": preview_url,
            "metadata": field_data,
            "sizes": sizes,
            "alternative_files": alternatives,
            "collections": collections,
        },
    }
    click.echo(json.dumps(output, indent=2))


def _print_resource_info(
    console: Console,
    resource_id: int,
    resource_data: dict[str, Any],
    field_data: list[dict[str, Any]],
    sizes: list[dict[str, Any]],
    alternatives: list[dict[str, Any]],
    collections: list[dict[str, Any]],
    preview_url: str,
) -> None:
    """Print formatted resource information using Rich."""
    console.print()
    console.print(
        Panel(f"[bold cyan]Resource #{resource_id}[/bold cyan]", expand=False)
    )

    # Basic Information section
    _print_basic_info(console, resource_data)

    # Preview URL section
    _print_preview_url(console, preview_url)

    # Metadata Fields table
    _print_metadata_table(console, field_data)

    # Available Sizes table
    _print_sizes_table(console, sizes)

    # Alternative Files table (if any)
    if alternatives:
        _print_alternatives_table(console, alternatives)

    # Collections table (if any)
    if collections:
        _print_collections_table(console, collections)

    console.print()


def _print_basic_info(console: Console, resource_data: dict[str, Any]) -> None:
    """Print basic resource information."""
    console.print()
    console.print("[bold]Basic Information[/bold]")
    console.print("-" * 20)

    # Resource type
    resource_type = resource_data.get("resource_type", "Unknown")
    console.print(f"  Type:        {resource_type}")

    # Created date
    created = resource_data.get("creation_date", "Unknown")
    console.print(f"  Created:     {created}")

    # File path/name
    file_path = resource_data.get("file_path", "") or resource_data.get(
        "original_filename", "Unknown"
    )
    console.print(f"  File:        {file_path}")

    # File extension
    extension = resource_data.get("file_extension", "Unknown")
    console.print(f"  Extension:   {extension}")

    # File size
    file_size = resource_data.get("file_size", 0)
    if file_size:
        file_size_str = _format_file_size(int(file_size))
        console.print(f"  File Size:   {file_size_str}")


def _print_preview_url(console: Console, preview_url: str) -> None:
    """Print preview URL section."""
    console.print()
    console.print("[bold]Preview URL[/bold]")
    console.print("-" * 20)
    if preview_url:
        console.print(f"  [blue]{preview_url}[/blue]")
    else:
        console.print("  [dim]No preview available[/dim]")


def _print_metadata_table(console: Console, field_data: list[dict[str, Any]]) -> None:
    """Print metadata fields as a table."""
    console.print()
    console.print("[bold]Metadata Fields[/bold]")
    console.print("-" * 20)

    if not field_data:
        console.print("  [dim]No metadata fields available[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Field", style="green")
    table.add_column("Value")

    for field in field_data:
        field_id = str(field.get("ref", field.get("resource_type_field", "?")))
        field_name = field.get("title", field.get("name", "Unknown"))
        field_value = field.get("value", "")

        # Truncate very long values for display
        if len(str(field_value)) > 100:
            field_value = str(field_value)[:97] + "..."

        table.add_row(field_id, str(field_name), str(field_value))

    console.print(table)


def _print_sizes_table(console: Console, sizes: list[dict[str, Any]]) -> None:
    """Print available sizes as a table."""
    console.print()
    console.print("[bold]Available Sizes[/bold]")
    console.print("-" * 20)

    if not sizes:
        console.print("  [dim]No size information available[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Size ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Width", justify="right")
    table.add_column("Height", justify="right")

    for size in sizes:
        size_id = str(size.get("id", size.get("size_code", "?")))
        name = size.get("name", size.get("size_name", "Unknown"))
        width = str(size.get("width", "-"))
        height = str(size.get("height", "-"))

        table.add_row(size_id, str(name), width, height)

    console.print(table)


def _print_alternatives_table(console: Console, alternatives: list[dict[str, Any]]) -> None:
    """Print alternative files as a table."""
    console.print()
    console.print("[bold]Alternative Files[/bold]")
    console.print("-" * 20)

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Extension")
    table.add_column("Size", justify="right")

    for alt in alternatives:
        alt_id = str(alt.get("ref", "?"))
        name = alt.get("name", alt.get("description", "Unknown"))
        extension = alt.get("file_extension", "-")
        file_size = alt.get("file_size", 0)
        size_str = _format_file_size(int(file_size)) if file_size else "-"

        table.add_row(alt_id, str(name), str(extension), size_str)

    console.print(table)


def _print_collections_table(console: Console, collections: list[dict[str, Any]]) -> None:
    """Print collections as a table."""
    console.print()
    console.print("[bold]Collections[/bold]")
    console.print("-" * 20)

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Resources", justify="right")

    for collection in collections:
        coll_id = str(collection.get("ref", collection.get("id", "?")))
        name = collection.get("name", "Unknown")
        count = str(collection.get("count", collection.get("c", "-")))

        table.add_row(coll_id, str(name), count)

    console.print(table)


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
