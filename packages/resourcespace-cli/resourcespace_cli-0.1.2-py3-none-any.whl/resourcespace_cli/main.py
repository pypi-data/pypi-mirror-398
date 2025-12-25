"""Main CLI entry point for ResourceSpace CLI."""

import click

from resourcespace_cli import __version__
from resourcespace_cli.commands.collections import collections
from resourcespace_cli.commands.config import config
from resourcespace_cli.commands.download import download
from resourcespace_cli.commands.info import info
from resourcespace_cli.commands.search import search
from resourcespace_cli.commands.types import types
from resourcespace_cli.commands.upload import upload


@click.group()
@click.version_option(version=__version__, prog_name="resourcespace-cli")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
@click.option("--no-color", "no_color", is_flag=True, help="Disable colored output")
@click.pass_context
def main(ctx: click.Context, json_output: bool, no_color: bool) -> None:
    """ResourceSpace CLI - Manage your ResourceSpace digital asset management system."""
    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json_output
    ctx.obj["no_color"] = no_color


# Register command groups
main.add_command(collections)
main.add_command(config)
main.add_command(download)
main.add_command(info)
main.add_command(search)
main.add_command(types)
main.add_command(upload)


if __name__ == "__main__":
    main()
