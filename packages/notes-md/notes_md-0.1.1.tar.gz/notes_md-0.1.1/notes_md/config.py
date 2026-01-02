"""
Configuration management.

Handles creation, reading, and writing of the application's YAML
configuration file stored in the user's home directory.
"""
from typing import Any, Dict
from pathlib import Path
import yaml
from .constants import config_dir, config_file


DEFAULT_CONFIG: Dict[str, Any] = {
    "notes_dir": str(Path.home() / "notes"),
}


def ensure_config() -> None:
    """
    Ensure the configuration directory and file exist.

    Creates the configuration directory if missing and writes a default
    configuration file if one does not already exist.
    """
    cfg_dir = config_dir()
    cfg_file = config_file()

    cfg_dir.mkdir(parents=True, exist_ok=True)

    if not cfg_file.exists():
        write_config(DEFAULT_CONFIG)

def read_config() -> Dict[str, Any]:
    """
    Read and return the application configuration.

    Ensures the configuration exists before loading it from disk.

    Returns:
        A dictionary containing configuration values.
    """
    ensure_config()
    with config_file().open("r") as f:
        return yaml.safe_load(f) or {}

def write_config(data: Dict[str, Any]) -> None:
    """
    Write configuration data to disk.

    Creates the configuration directory if necessary and overwrites the
    existing configuration file with the provided data.
    """
    cfg_dir = config_dir()
    cfg_dir.mkdir(parents=True, exist_ok=True)

    with config_file().open("w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
