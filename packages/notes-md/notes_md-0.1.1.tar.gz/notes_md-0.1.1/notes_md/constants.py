"""
Shared constants for notes_md configuration and paths.
"""
from pathlib import Path

APP_NAME = "notes_md"

def config_dir() -> Path:
    """
    Return the path to the application's configuration directory.

    This directory is located at:
        $HOME/.config/<APP_NAME>

    Returns:
        Path: Path object pointing to the configuration directory.
    """
    return Path.home() / ".config" / APP_NAME

def config_file() -> Path:
    """
    Return the path to the application's configuration file.

    The configuration file is located inside the config directory:
        $HOME/.config/<APP_NAME>/config.yaml

    Returns:
        Path: Path object pointing to the configuration file.
    """
    return config_dir() / "config.yaml"
