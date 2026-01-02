"""
Click command for creating and opening a new project note.
"""
from pathlib import Path
import click
from ..helpers import open_editor, create_note_directory
from ..config import read_config

@click.command(name="add")
@click.argument("note_name")
def add_note(note_name: str):
    """
    Create a new note for the current working directory and open it in $EDITOR.

    NOTE_NAME should NOT include the file extension (e.g., meeting).
    """
    project_dir = create_note_directory()  # will create the folder if missing

    if project_dir is None:
        # Already exists — get path anyway
        config = read_config()
        project_dir = Path(config["notes_dir"]) / Path.cwd().name

    note_name = f"{note_name}.md"
    note_path = project_dir / note_name

    # Ensure file exists and open it
    note_path.touch(exist_ok=True)
    click.echo(f"Opening note: {note_path}")
    open_editor(note_path)
