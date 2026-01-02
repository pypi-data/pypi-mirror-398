from pathlib import Path
from notes_md.config import write_config
from notes_md.helpers import create_note_directory

def test_create_note_directory_creates_project_dir(temp_home, monkeypatch):
    project_dir = temp_home / "project_1"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Override config to use temp_home
    write_config({"notes_dir": str(temp_home / "notes")})

    # Ensure notes directory does NOT exist yet
    notes_root = temp_home / "notes"
    assert not notes_root.exists()

    notes_dir = create_note_directory()

    assert notes_dir is not None
    assert notes_dir.exists()

def test_creae_note_directory_returns_none_if_exists(temp_home, monkeypatch):
    project_dir = temp_home / "project_2"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Override config to use temp_home
    write_config({"notes_dir": str(temp_home / "notes")})

    first = create_note_directory()
    second = create_note_directory()

    assert first is not None
    assert second is None
