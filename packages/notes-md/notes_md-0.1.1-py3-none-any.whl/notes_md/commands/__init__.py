"""
Command registry for notes_md.

Collects and exposes all Click command functions used by the CLI.
"""
from .init import init
from .list import list_notes
from .open import open_note
from .add import add_note
from .notebooks import list_notebooks
from .sync import sync
from .remove import remove_note

__all__ = [
    "init",
    "list_notes",
    "open_note",
    "add_note",
    "list_notebooks",
    "sync",
    "remove_note"
]
