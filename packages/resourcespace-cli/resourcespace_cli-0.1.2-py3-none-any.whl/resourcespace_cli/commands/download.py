"""Download command for ResourceSpace CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from resourcespace_cli.api.resources import get_resource_data, get_resource_path
from resourcespace_cli.api.search import do_search
from resourcespace_cli.client import ResourceSpaceClient
from resourcespace_cli.config import load_config
from resourcespace_cli.output import get_console
from resourcespace_cli.utils.errors import BatchResult, handle_exception
from resourcespace_cli.utils.files import (
    ensure_output_directory,
    extract_filename_from_url,
    resolve_filename_conflict,
    sanitize_filename,
)
from resourcespace_cli.utils.validation import validate_download_input


@click.command()
@click.argument("resource_id", type=int, required=False)
@click.option(
    "--search",
    "search_query",
    type=str,
    default=None,
    help="Download all resources matching this search query.",
)
@click.option(
    "--output",
    "-o",
    "output_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for downloaded files (default: current directory).",
)
@click.option(
    "--stdout",
    is_flag=True,
    default=False,
    help="Output file contents to stdout (single resource only).",
)
@click.pass_context
def download(
    ctx: click.Context,
    resource_id: int | None,
    search_query: str | None,
    output_dir: Path | None,
    stdout: bool,
) -> None:
    """Download resources from ResourceSpace.

    Download a single resource by ID, or use --search to download
    all matching resources in batch.

    \b
    Examples:
        rs download 12345
        rs download 12345 --output ./downloads
        rs download 12345 --stdout > file.jpg
        rs download --search "landscape" --output ./batch
    """
    json_output: bool = ctx.obj.get("json_output", False)
    console = get_console(ctx)

    try:
        # Validate input before making API calls
        validated = validate_download_input(
            resource_id=resource_id,
            search_query=search_query,
            output_dir=output_dir,
            stdout=stdout,
        )

        config = load_config()

        with ResourceSpaceClient(config) as client:
            if validated.resource_id is not None:
                # Single resource download
                _download_single(
                    console,
                    client,
                    validated.resource_id,
                    validated.output_dir,
                    validated.stdout,
                    json_output,
                )
            else:
                # Batch download via search
                assert validated.search_query is not None  # Type narrowing
                _download_batch(
                    ctx, console, client, validated.search_query, validated.output_dir, json_output
                )

    except Exception as e:
        handle_exception(ctx, e)


def _download_single(
    console: Console,
    client: ResourceSpaceClient,
    resource_id: int,
    output_dir: Path,
    stdout: bool,
    json_output: bool,
) -> None:
    """Download a single resource."""
    # Get resource metadata for filename
    resource_data = get_resource_data(client, resource_id)

    # Get download URL
    download_url = get_resource_path(client, resource_id)

    # Determine filename from resource data
    filename = _get_filename(resource_data, download_url, resource_id)

    if stdout:
        # Stream to stdout
        _stream_to_stdout(client, download_url)
    else:
        # Download to file
        ensure_output_directory(output_dir)
        filepath = resolve_filename_conflict(output_dir, filename, resource_id)
        _download_with_progress(console, client, download_url, filepath, json_output)

        if json_output:
            click.echo(
                json.dumps(
                    {
                        "status": "success",
                        "resource_id": resource_id,
                        "file": str(filepath),
                    },
                    indent=2,
                )
            )
        else:
            console.print(f"[green]Downloaded:[/green] {filepath}")


def _download_batch(
    ctx: click.Context,
    console: Console,
    client: ResourceSpaceClient,
    search_query: str,
    output_dir: Path,
    json_output: bool,
) -> None:
    """Download all resources matching a search query."""
    # Search for resources (fetch all results)
    results = do_search(client, search_query, limit=9999)

    if not results:
        if json_output:
            click.echo(
                json.dumps(
                    {
                        "status": "success",
                        "query": search_query,
                        "message": "No resources found",
                        "downloaded": 0,
                    },
                    indent=2,
                )
            )
        else:
            console.print(f"[dim]No resources found for '{search_query}'[/dim]")
        return

    ensure_output_directory(output_dir)

    batch_result = BatchResult()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        disable=json_output,
    ) as progress:
        task = progress.add_task(
            f"Downloading {len(results)} files...", total=len(results)
        )

        for resource in results:
            res_id: int = int(resource.get("ref", resource.get("id", 0)))
            try:
                download_url = get_resource_path(client, res_id)

                # Determine filename
                filename = _get_filename(resource, download_url, res_id)
                filepath = resolve_filename_conflict(output_dir, filename, res_id)

                _download_file(client, download_url, filepath)
                batch_result.add_success({"id": res_id, "file": str(filepath)})

            except Exception as e:
                batch_result.add_failure(res_id, str(e))

            progress.update(task, advance=1)

    # Report results
    if json_output:
        output = batch_result.to_dict()
        output["query"] = search_query
        click.echo(json.dumps(output, indent=2))
    else:
        batch_result.print_summary(ctx, item_type="file")

    # Exit with appropriate code based on results
    if batch_result.all_failed:
        ctx.exit(1)


def _get_filename(
    resource_data: dict[str, Any], download_url: str, resource_id: int
) -> str:
    """Extract and sanitize filename from resource data or URL."""
    # Try to get original filename from resource data
    original_filename = resource_data.get("file_path", "") or resource_data.get(
        "original_filename", ""
    )

    if not original_filename:
        original_filename = extract_filename_from_url(download_url)

    # If still no filename, create one based on resource ID
    if not original_filename or original_filename == "download":
        extension = resource_data.get("file_extension", "")
        if extension:
            original_filename = f"resource_{resource_id}.{extension}"
        else:
            original_filename = f"resource_{resource_id}"

    return sanitize_filename(Path(original_filename).name)


def _download_with_progress(
    console: Console,
    client: ResourceSpaceClient,
    url: str,
    filepath: Path,
    json_output: bool,
) -> None:
    """Download a file with a progress bar."""
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        disable=json_output,
    ) as progress:
        task = progress.add_task(f"Downloading {filepath.name}...", total=None)

        with open(filepath, "wb") as f:
            for chunk, total_size in client.download_stream(url):
                if total_size and progress.tasks[task].total != total_size:
                    progress.update(task, total=total_size)
                f.write(chunk)
                progress.update(task, advance=len(chunk))


def _download_file(client: ResourceSpaceClient, url: str, filepath: Path) -> None:
    """Download a file without progress display (for batch mode)."""
    with open(filepath, "wb") as f:
        for chunk, _ in client.download_stream(url):
            f.write(chunk)


def _stream_to_stdout(client: ResourceSpaceClient, url: str) -> None:
    """Stream file contents to stdout."""
    for chunk, _ in client.download_stream(url):
        sys.stdout.buffer.write(chunk)
