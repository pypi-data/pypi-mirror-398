"""Configuration commands for ResourceSpace CLI."""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from resourcespace_cli.config import (
    clear_config,
    get_config_value,
    get_env_path,
    load_config,
    resolve_key_alias,
    set_config_value,
)
from resourcespace_cli.output import get_console
from resourcespace_cli.utils.errors import handle_exception


@click.group()
def config() -> None:
    """Manage ResourceSpace CLI configuration."""


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """Set a configuration value.

    KEY is the configuration key (url, key, user, or full name).
    VALUE is the value to set.

    \b
    Examples:
        rs config set url https://resourcespace.example.com
        rs config set key abc123def456
        rs config set user admin
    """
    json_output: bool = ctx.obj.get("json_output", False)

    try:
        resolved_key = resolve_key_alias(key)
        set_config_value(resolved_key, value)

        if json_output:
            click.echo(
                json.dumps(
                    {
                        "status": "success",
                        "key": resolved_key,
                        "message": f"Configuration '{resolved_key}' has been set",
                    }
                )
            )
        else:
            console = get_console(ctx)
            console.print(f"[green]Successfully set[/green] [bold]{resolved_key}[/bold]")

    except Exception as e:
        handle_exception(ctx, e)


@config.command("get")
@click.argument("key", required=False)
@click.option(
    "--show-values", "-s", is_flag=True, help="Show actual values (WARNING: exposes secrets)"
)
@click.pass_context
def config_get(ctx: click.Context, key: str | None, show_values: bool) -> None:
    """Get configuration values.

    If KEY is provided, shows that specific value.
    If KEY is omitted, shows all configuration values.

    By default, sensitive values are masked. Use --show-values to reveal them.

    \b
    Examples:
        rs config get
        rs config get url
        rs config get --show-values
    """
    json_output: bool = ctx.obj.get("json_output", False)

    try:
        if key:
            resolved_key = resolve_key_alias(key)
            value = get_config_value(resolved_key)

            if json_output:
                click.echo(
                    json.dumps(
                        {
                            "key": resolved_key,
                            "value": value,
                            "is_set": value is not None,
                        }
                    )
                )
            else:
                console = get_console(ctx)
                if value is None:
                    console.print(f"[yellow]{resolved_key}[/yellow]: [dim]not set[/dim]")
                else:
                    display_value = _mask_value(resolved_key, value, show_values)
                    console.print(f"[bold]{resolved_key}[/bold]: {display_value}")
        else:
            config_obj = load_config()
            config_dict = config_obj.to_dict()
            env_path = get_env_path()

            if json_output:
                output = {
                    "config_file": str(env_path),
                    "config_file_exists": env_path.exists(),
                    "values": {
                        k: {"value": v, "is_set": v is not None} for k, v in config_dict.items()
                    },
                    "is_complete": config_obj.is_complete(),
                }
                click.echo(json.dumps(output, indent=2))
            else:
                console = get_console(ctx)
                _print_config_table(console, config_dict, env_path, show_values)

                if not config_obj.is_complete():
                    console.print()
                    console.print(
                        "[yellow]Warning:[/yellow] Configuration is incomplete. "
                        "Set all values to use the CLI."
                    )

    except Exception as e:
        handle_exception(ctx, e)


@config.command("clear")
@click.argument("key", required=False)
@click.option("--all", "-a", "clear_all", is_flag=True, help="Clear all configuration values")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def config_clear(
    ctx: click.Context,
    key: str | None,
    clear_all: bool,
    yes: bool,
) -> None:
    """Clear configuration values.

    If KEY is provided, clears that specific value.
    Use --all to clear all configuration values.

    \b
    Examples:
        rs config clear url
        rs config clear --all
        rs config clear --all --yes
    """
    json_output: bool = ctx.obj.get("json_output", False)

    if not key and not clear_all:
        from resourcespace_cli.exceptions import ValidationError

        handle_exception(
            ctx, ValidationError("Specify a KEY to clear, or use --all to clear all values")
        )

    try:
        resolved_key: str | None = None
        if key:
            resolved_key = resolve_key_alias(key)

        console = get_console(ctx)

        # Confirmation prompt (skip in JSON mode or if --yes)
        if not json_output and not yes:
            if clear_all:
                msg = "Are you sure you want to clear ALL configuration values?"
            else:
                msg = f"Are you sure you want to clear '{resolved_key}'?"

            if not click.confirm(msg):
                console.print("[dim]Cancelled.[/dim]")
                return

        cleared = clear_config(resolved_key)

        if json_output:
            click.echo(
                json.dumps(
                    {
                        "status": "success",
                        "cleared": cleared,
                        "count": len(cleared),
                    }
                )
            )
        else:
            if cleared:
                for k in cleared:
                    console.print(f"[green]Cleared[/green] [bold]{k}[/bold]")
            else:
                console.print("[dim]No configuration values were set.[/dim]")

    except Exception as e:
        handle_exception(ctx, e)


def _mask_value(key: str, value: str, show: bool) -> str:
    """Mask sensitive configuration values.

    Args:
        key: Configuration key name.
        value: The actual value.
        show: If True, return the actual value.

    Returns:
        The value or a masked representation.
    """
    if show:
        return value

    # Mask API key completely
    if "API_KEY" in key:
        if len(value) <= 8:
            return "****"
        return value[:4] + "****" + value[-4:]

    # Don't mask URL or username
    return value


def _print_config_table(
    console: Console,
    config_dict: dict[str, str | None],
    env_path: Path,
    show_values: bool,
) -> None:
    """Print configuration as a Rich table.

    Args:
        console: Rich Console instance.
        config_dict: Dictionary of configuration key-value pairs.
        env_path: Path to the .env file.
        show_values: Whether to show unmasked values.
    """
    table = Table(title="ResourceSpace CLI Configuration")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_column("Status", style="dim")

    for key, value in config_dict.items():
        if value is None:
            table.add_row(key, "[dim]not set[/dim]", "[yellow]Missing[/yellow]")
        else:
            display_value = _mask_value(key, value, show_values)
            table.add_row(key, display_value, "[green]Set[/green]")

    console.print()
    console.print(f"[dim]Config file: {env_path}[/dim]")
    console.print()
    console.print(table)
