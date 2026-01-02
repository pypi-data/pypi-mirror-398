"""
Main CLI entrypoint for notes_md.

Initializes configuration, defines the root Click command group,
and registers all note-management subcommands.
"""
import click
from .config import ensure_config
from .commands import init, list_notes, open_note, add_note, list_notebooks, sync, remove_note


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
def cli(ctx: click.Context):
    """
    Root command group for the notes_md CLI.

    This function initializes the application runtime by ensuring the
    configuration directory and file exist, and by preparing a shared
    context object for all subcommands.
    """
    ensure_config()
    ctx.ensure_object(dict)


cli.add_command(init)
cli.add_command(list_notes)
cli.add_command(open_note)
cli.add_command(add_note)
cli.add_command(list_notebooks)
cli.add_command(sync)
cli.add_command(remove_note)
