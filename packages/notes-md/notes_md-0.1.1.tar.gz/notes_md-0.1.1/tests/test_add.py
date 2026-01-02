from pathlib import Path
import pytest
from click.testing import CliRunner
from notes_md.cli import cli
from notes_md.config import write_config

@pytest.fixture
def runner():
    return CliRunner()

def test_add_creates_note_file(temp_home, runner, monkeypatch):
    # Override config to use temp notes dir
    notes_dir = temp_home / "notes"
    write_config({"notes_dir": str(notes_dir)})

    # Patch open_editor to avoid opening editor
    monkeypatch.setattr("notes_md.commands.add.open_editor", lambda path: None)

    # Simulate current project folder
    project_dir = temp_home / "my_project"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Run CLI
    result = runner.invoke(cli, ["add", "meeting"])
    
    # Assertions
    assert result.exit_code == 0
    note_file = notes_dir / "my_project" / "meeting.md"
    assert note_file.exists()
    assert "Opening note" in result.output

def test_add_existing_note(temp_home, runner, monkeypatch):
    # Override config to use temp notes dir
    notes_dir = temp_home / "notes"
    write_config({"notes_dir": str(notes_dir)})

    # Patch open_editor to avoid opening editor
    monkeypatch.setattr("notes_md.commands.add.open_editor", lambda path: None)

    # Simulate current project folder
    project_dir = temp_home / "my_project2"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Create the note manually
    note_file = notes_dir / "my_project2" / "meeting.md"
    note_file.parent.mkdir(parents=True, exist_ok=True)
    note_file.touch()

    # Run CLI
    result = runner.invoke(cli, ["add", "meeting"])
    
    assert result.exit_code == 0
    # Should still open it without error
    assert "Opening note" in result.output
