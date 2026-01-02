"""
Click command for creating a new project directory.
"""
import click
from ..helpers import create_note_directory


@click.command()
def init():
    """
    Initialize a notes directory for the current working directory.

    Creates a project-specific notes folder under the configured notes
    root. If the notes directory already exists, no changes are made.
    """
    notes_dir = create_note_directory()

    if notes_dir is not None:
        click.echo(
            f"Initialized notes for this directory.\n"
            f"Notes located: {notes_dir}"
        )
    else:
        click.echo("Notes directory already initialized")
