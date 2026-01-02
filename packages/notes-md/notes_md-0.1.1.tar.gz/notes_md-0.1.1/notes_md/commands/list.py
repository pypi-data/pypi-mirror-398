"""
Click command for listing all notes of the current working directory
"""
from pathlib import Path
import click
from ..helpers import open_editor
from ..config import read_config

@click.command(name="list")
def list_notes():
    """
    List notes for the current working directory with numeric IDs and open the selected note.
    """
    config = read_config()
    project_dir = Path(config["notes_dir"]) / Path.cwd().name

    if not project_dir.exists():
        click.echo("No notes directory initialized for this project.")
        return

    # Get all .md files in the project folder
    notes = sorted(p for p in project_dir.iterdir() if p.is_file() and p.suffix == ".md")

    if not notes:
        click.echo("No notes found.")
        return

    # Display notes with numeric IDs
    click.echo("Notes:")
    for idx, note in enumerate(notes, start=1):
        click.echo(f"{idx}: {note.stem}")

    # Prompt for selection by ID
    def validate_choice(value):
        try:
            ivalue = int(value)
        except ValueError as exc:
            raise click.BadParameter("Please enter a number.") from exc
        if ivalue < 1 or ivalue > len(notes):
            raise click.BadParameter(f"Enter a number between 1 and {len(notes)}.")
        return ivalue

    selected_id = click.prompt(
        "Select a note to open",
        value_proc=validate_choice
    )

    selected_path = notes[selected_id - 1]
    open_editor(selected_path)
