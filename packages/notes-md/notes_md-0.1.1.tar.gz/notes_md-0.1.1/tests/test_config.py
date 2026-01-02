from pathlib import Path
from notes_md.config import ensure_config, read_config
from notes_md.constants import config_dir, config_file

def test_ensure_config_creates_files(temp_home):
    ensure_config()

    cfg_dir = config_dir()
    cfg_file = config_file()
    assert cfg_dir.exists()
    assert cfg_file.exists()

def test_read_config_returns_defaults(temp_home):
    config = read_config()

    assert "notes_dir" in config
    assert Path(config["notes_dir"]).exists()
