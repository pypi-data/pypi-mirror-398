"""Upload command for ResourceSpace CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
)

from resourcespace_cli.api.upload import (
    add_resource_to_collection,
    create_resource,
    update_field,
    upload_file,
)
from resourcespace_cli.client import ResourceSpaceClient
from resourcespace_cli.config import load_config
from resourcespace_cli.output import get_console
from resourcespace_cli.utils.errors import BatchResult, handle_exception
from resourcespace_cli.utils.validation import validate_field_string, validate_upload_input


def _parse_field(field_str: str) -> tuple[str, str]:
    """Parse a field string in the format 'name=value'.

    Args:
        field_str: Field string like 'title=My Photo'.

    Returns:
        Tuple of (field_name, field_value).

    Raises:
        click.BadParameter: If format is invalid.
    """
    if "=" not in field_str:
        raise click.BadParameter(
            f"Invalid field format '{field_str}'. Use 'name=value' format."
        )
    name, _, value = field_str.partition("=")
    return name.strip(), value.strip()


def _expand_files(file_args: tuple[str, ...], use_stdin: bool) -> list[Path]:
    """Expand file arguments including glob patterns.

    Args:
        file_args: File paths or glob patterns.
        use_stdin: If True, read file paths from stdin.

    Returns:
        List of resolved file paths.
    """
    files: list[Path] = []

    if use_stdin:
        for line in sys.stdin:
            line = line.strip()
            if line:
                path = Path(line)
                if path.is_file():
                    files.append(path.resolve())

    for pattern in file_args:
        path = Path(pattern)

        # Check if it's a glob pattern
        if "*" in pattern or "?" in pattern:
            # Use glob for pattern matching (supports ** for recursive)
            if "**" in pattern:
                # For recursive patterns, need to split base and pattern
                matches = list(Path.cwd().glob(pattern))
            else:
                matches = list(Path.cwd().glob(pattern))

            for match in matches:
                if match.is_file():
                    files.append(match.resolve())
        elif path.is_file():
            files.append(path.resolve())

    return files


def _upload_single(
    client: ResourceSpaceClient,
    filepath: Path,
    resource_type: int,
    collection_id: int | None,
    fields: list[tuple[str, str]],
) -> dict[str, Any]:
    """Upload a single file.

    Args:
        client: ResourceSpace API client.
        filepath: Path to file to upload.
        resource_type: Resource type ID.
        collection_id: Optional collection ID.
        fields: List of (field_name, value) tuples.

    Returns:
        Result dictionary with file, resource_id, and status.
    """
    # Create the resource
    resource_id = create_resource(client, resource_type)

    # Upload the file
    upload_file(client, resource_id, filepath)

    # Set metadata fields (fields are specified by name, we'd need to resolve to ID)
    # For now, we assume field names are numeric IDs
    for field_name, field_value in fields:
        try:
            field_id = int(field_name)
            update_field(client, resource_id, field_id, field_value)
        except ValueError:
            # Field name is not numeric - skip for now
            # TODO: Resolve field name to ID using get_resource_type_fields
            pass

    # Add to collection if specified
    if collection_id is not None:
        add_resource_to_collection(client, resource_id, collection_id)

    return {
        "file": str(filepath),
        "resource_id": resource_id,
        "status": "success",
    }


@click.command()
@click.argument("files", nargs=-1, type=str)
@click.option(
    "--type",
    "-t",
    "resource_type",
    type=int,
    default=1,
    help="Resource type ID (default: 1).",
)
@click.option(
    "--collection",
    "-c",
    "collection_id",
    type=int,
    default=None,
    help="Add uploaded resources to this collection.",
)
@click.option(
    "--field",
    "-f",
    "fields",
    multiple=True,
    help="Set metadata field: --field 'field_id=value'. Can be repeated.",
)
@click.option(
    "--stdin",
    "use_stdin",
    is_flag=True,
    default=False,
    help="Read file paths from stdin (one per line).",
)
@click.pass_context
def upload(
    ctx: click.Context,
    files: tuple[str, ...],
    resource_type: int,
    collection_id: int | None,
    fields: tuple[str, ...],
    use_stdin: bool,
) -> None:
    """Upload files to ResourceSpace.

    Upload one or more files as new resources. Supports glob patterns
    for batch uploads and reading file paths from stdin.

    \b
    Examples:
        rs upload photo.jpg
        rs upload photo.jpg --type 2 --collection 5
        rs upload photo.jpg --field "8=My Title" --field "3=Description"
        rs upload *.jpg
        rs upload photos/**/*.jpg
        find . -name "*.jpg" | rs upload --stdin
    """
    json_output: bool = ctx.obj.get("json_output", False)
    console = get_console(ctx)

    try:
        # Parse and validate field options
        parsed_fields: list[tuple[str, str]] = []
        for field_str in fields:
            parsed_fields.append(validate_field_string(field_str))

        # Expand file arguments
        file_paths = _expand_files(files, use_stdin)

        # Validate upload input
        validated = validate_upload_input(
            files=file_paths,
            resource_type=resource_type,
            collection_id=collection_id,
            fields=parsed_fields,
        )

        config = load_config()

        with ResourceSpaceClient(config) as client:
            if len(validated.files) == 1:
                # Single file upload
                result = _upload_single(
                    client,
                    validated.files[0],
                    validated.resource_type,
                    validated.collection_id,
                    validated.fields,
                )

                if json_output:
                    click.echo(json.dumps(result, indent=2))
                else:
                    console.print(
                        f"[green]Uploaded:[/green] {validated.files[0].name} → "
                        f"Resource ID {result['resource_id']}"
                    )
            else:
                # Batch upload
                _upload_batch(
                    ctx,
                    console,
                    client,
                    validated.files,
                    validated.resource_type,
                    validated.collection_id,
                    validated.fields,
                    json_output,
                )

    except Exception as e:
        handle_exception(ctx, e)


def _upload_batch(
    ctx: click.Context,
    console: Console,
    client: ResourceSpaceClient,
    file_paths: list[Path],
    resource_type: int,
    collection_id: int | None,
    fields: list[tuple[str, str]],
    json_output: bool,
) -> None:
    """Upload multiple files with progress display.

    Args:
        ctx: Click context.
        console: Rich Console instance.
        client: ResourceSpace API client.
        file_paths: List of file paths to upload.
        resource_type: Resource type ID.
        collection_id: Optional collection ID.
        fields: List of (field_name, value) tuples.
        json_output: Whether to output JSON.
    """
    batch_result = BatchResult()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        disable=json_output,
    ) as progress:
        task = progress.add_task(
            f"Uploading {len(file_paths)} files...", total=len(file_paths)
        )

        for filepath in file_paths:
            try:
                result = _upload_single(
                    client,
                    filepath,
                    resource_type,
                    collection_id,
                    fields,
                )
                batch_result.add_success(result)
            except Exception as e:
                batch_result.add_failure(str(filepath), str(e))

            progress.update(task, advance=1)

    # Report results
    if json_output:
        batch_result.output_json()
    else:
        batch_result.print_summary(ctx, item_type="file")

    # Exit with appropriate code based on results
    if batch_result.all_failed:
        ctx.exit(1)
