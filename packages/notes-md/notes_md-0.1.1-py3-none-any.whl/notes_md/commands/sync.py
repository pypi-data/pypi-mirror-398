"""
Click command for syncing with git.
"""
from pathlib import Path
import click
from ..helpers import run_git_command, git_has_changes
from ..config import read_config


@click.command(name="sync")
@click.option("--message", "-m", default="Update notes", help="Commit message")
def sync(message: str):
    """
    Sync the notes directory with Git (pull, commit, push).

    Automatically pulls remote changes, commits all local changes with a message,
    and pushes to the remote repository.
    """
    config = read_config()
    notes_dir = Path(config["notes_dir"])

    # Ensure it's a git repository
    if not (notes_dir / ".git").exists():
        click.echo(f"{notes_dir} is not a git repository. Initialize with 'git init'.")
        return

    # No changes guard
    if not git_has_changes(notes_dir):
        click.echo("Nothing to sync.")
        return

    # Add all changes
    click.echo("Adding all changes...")
    run_git_command(["add", "--all"], notes_dir)

    # Commit changes
    click.echo(f"Committing changes with message: '{message}'")
    try:
        run_git_command(["commit", "-m", message], notes_dir)
    except click.Abort:
        click.echo("No changes to commit.")

    # Pull latest
    click.echo("Pulling latest changes...")
    run_git_command(["pull"], notes_dir)

    # Push
    click.echo("Pushing to remote...")
    run_git_command(["push"], notes_dir)

    click.echo("Sync complete!")
