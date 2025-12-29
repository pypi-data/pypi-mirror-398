"""
GitHub Contribution Writer

A CLI tool to draw words on your GitHub contribution graph.
"""

__version__ = "1.0.0"

from contribution_writer.cli import main
from contribution_writer.font import FONT, word_to_grid

__all__ = ["main", "FONT", "word_to_grid", "__version__"]
