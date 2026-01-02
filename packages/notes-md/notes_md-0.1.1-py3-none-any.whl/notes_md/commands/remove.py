"""
Click command for removing a note.
"""
from pathlib import Path
import click
from ..config import read_config
from ..helpers import run_git_command


@click.command(name="remove")
@click.argument("note_name")
def remove_note(note_name: str):
    """
    Remove a note for the current working directory.

    NOTE_NAME should be provided without extension; '.md' is appended automatically.
    The note will be removed with 'git rm' so it can be synced.
    """
    note_name = f"{note_name}.md"
    config = read_config()
    notes_dir = Path(config["notes_dir"])
    project_dir = Path(config["notes_dir"]) / Path.cwd().name
    note_path = project_dir / note_name

    if not note_path.exists():
        click.echo(f"Note '{note_name}' does not exist.")
        return

    if not (notes_dir / ".git").exists():
        click.echo(f"{notes_dir} is not a git repository. Initialize with 'git init'.")
        return

    # Confirm removal
    if not click.confirm(f"Are you sure you want to remove '{note_name}'?"):
        click.echo("Aborted.")
        return

    # Run git rm
    run_git_command(["rm", str(note_path)], notes_dir)
    click.echo(f"Removed note: {note_name}. Remember to 'notes_md sync' to push changes.")
