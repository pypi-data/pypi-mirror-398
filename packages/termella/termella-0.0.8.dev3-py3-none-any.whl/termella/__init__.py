"""
Termella - Rich text and beautiful formatting in the terminal.
Version: 0.0.8.dev3
"""

from .printer import cprint, cinput
from .core import Text
from .widgets import panel, progress_bar, table, Spinner, select, checkbox, tree, columns, grid
from .live import Live
from .markup import parse, print_tag, add_alias
from .app import App

__version__ = "0.0.8.dev3"
__all__ = [
    "cprint", "cinput", "Text", 
    "panel", "progress_bar", "table", "Spinner", 
    "select", "checkbox", "tree", "columns", "grid",
    "Live",
    "parse", "print_tag", "add_alias",
    "App"
]