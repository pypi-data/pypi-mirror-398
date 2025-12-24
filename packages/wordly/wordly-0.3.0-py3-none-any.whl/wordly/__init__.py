"""Wordly.

A simple python client that requests dictionary definitions
from a server that implements Dictionary Server Protocol.
"""

from __future__ import annotations

from wordly.words import Word

__app_name__ = "Wordly"
__app_description__ = (
    "A simple python client that requests dictionary definitions"
    " from a server that implements Dictionary Server Protocol."
)
__epilog__ = "Stay in the know."
__version__ = "0.3.0"

__all__ = ["Word"]
