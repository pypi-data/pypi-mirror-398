"""
Click command for opening a note.
"""
from pathlib import Path
import click
from ..helpers import open_editor
from ..config import read_config

@click.command(name="open")
@click.argument("note_name")
def open_note(note_name: str):
    """
    Open a note for the current project in the user's $EDITOR.
    """
    config = read_config()
    project_dir = Path(config["notes_dir"]) / Path.cwd().name
    # Append .md extension
    note_name = f"{note_name}.md"
    note_path = project_dir / note_name

    if not note_path.exists():
        click.echo(f"Note '{note_name}' does not exist.")
        return

    open_editor(note_path)
