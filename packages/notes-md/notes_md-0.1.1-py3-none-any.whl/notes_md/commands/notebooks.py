"""
Click command for listing a projects you currently have a notes directory for
"""
from pathlib import Path
import click
from ..helpers import open_editor
from ..config import read_config


@click.command(name="books")
def list_notebooks():
    """
    List all top-level projects (notebooks) and open selected folder in $EDITOR.
    """
    config = read_config()
    notes_root = Path(config["notes_dir"])

    if not notes_root.exists() or not any(notes_root.iterdir()):
        click.echo(f"No projects found in {notes_root}")
        return

    # Get all directories
    projects = sorted([p for p in notes_root.iterdir() if p.is_dir()])

    if not projects:
        click.echo(f"No projects found in {notes_root}")
        return

    # Display projects with numeric IDs
    click.echo("Notebooks / Projects:")
    for idx, project in enumerate(projects, start=1):
        click.echo(f"{idx}: {project.name}")

    # Prompt for selection
    def validate_choice(value):
        try:
            ivalue = int(value)
        except ValueError as exc:
            raise click.BadParameter("Please enter a number.") from exc
        if ivalue < 1 or ivalue > len(projects):
            raise click.BadParameter(f"Enter a number between 1 and {len(projects)}.")
        return ivalue

    selected_id = click.prompt(
        "Select a notebook/project to open by number",
        value_proc=validate_choice
    )

    selected_path = projects[selected_id - 1]
    click.echo(f"Opening {selected_path} in $EDITOR...")
    open_editor(selected_path)
