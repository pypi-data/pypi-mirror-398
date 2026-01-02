"""
Shared helpers for managing note directories, opening notes in the editor,
and interacting with Git.

Provides filesystem utilities for creating per-project note
directories, helpers for opening notes using $EDITOR, and thin wrappers around
common Git operations used by the CLI commands.
"""
import os
import subprocess
from pathlib import Path
import click
from .config import read_config


def create_note_directory() -> Path or None:
    """
    Create a note directory for the current working directory.

    Returns the created Path, or None if it already exists.
    """
    config = read_config()

    base_dir = Path(config["notes_dir"])
    project_name = Path.cwd().name
    dir_path = base_dir / project_name

    if dir_path.exists():
        return None

    dir_path.mkdir(parents=True)
    return dir_path

def open_editor(path: Path):
    """
    Open the given path in the user's $EDITOR.
    If $EDITOR is a terminal editor, opens directory listing.
    GUI editors (VSCode, Sublime) will open the folder.
    """
    editor = os.environ.get("EDITOR", "nano")
    try:
        subprocess.run([editor, str(path)], check=True)
    except FileNotFoundError:
        click.echo(f"Editor '{editor}' not found. Set $EDITOR to your preferred editor.")

def run_git_command(args, cwd: Path):
    """Run a git command in the given directory."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True
    )
    if result.returncode != 0:
        click.echo(f"Error running git {' '.join(args)}:\n{result.stderr}")
        raise click.Abort()
    return result.stdout.strip()

def git_has_changes(cwd: Path) -> bool:
    """
    Return True if there are any staged or unstaged changes in the repo.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True
    )
    return bool(result.stdout.strip())
