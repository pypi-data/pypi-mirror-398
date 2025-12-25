"""Output formatting utilities for ResourceSpace CLI."""

from __future__ import annotations

import json

import click
from rich.console import Console
from rich.table import Table


def get_console(ctx: click.Context | None = None) -> Console:
    """Get a Console instance respecting the --no-color flag.

    Args:
        ctx: Click context containing no_color flag.

    Returns:
        Configured Console instance.
    """
    no_color = False
    if ctx is not None:
        no_color = ctx.obj.get("no_color", False)

    return Console(no_color=no_color)


def print_error(
    ctx: click.Context,
    message: str,
    error_type: str = "Error",
) -> None:
    """Print an error message in red or as JSON.

    Args:
        ctx: Click context.
        message: Error message to display.
        error_type: Type of error (e.g., "API Error", "Configuration Error").
    """
    json_output = ctx.obj.get("json_output", False)
    if json_output:
        click.echo(json.dumps({"status": "error", "message": message}))
    else:
        console = get_console(ctx)
        console.print(f"[red]{error_type}:[/red] {message}")


def print_success(ctx: click.Context, message: str) -> None:
    """Print a success message in green.

    Args:
        ctx: Click context.
        message: Success message to display.
    """
    console = get_console(ctx)
    console.print(f"[green]{message}[/green]")


def print_table(ctx: click.Context, table: Table) -> None:
    """Print a Rich table respecting color settings.

    Args:
        ctx: Click context.
        table: Rich Table to print.
    """
    console = get_console(ctx)
    console.print(table)


def print_dim(ctx: click.Context, message: str) -> None:
    """Print a dim/muted message.

    Args:
        ctx: Click context.
        message: Message to display.
    """
    console = get_console(ctx)
    console.print(f"[dim]{message}[/dim]")
