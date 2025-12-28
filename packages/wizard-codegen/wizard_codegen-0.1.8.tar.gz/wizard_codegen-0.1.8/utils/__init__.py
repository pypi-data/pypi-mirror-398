"""
Utility functions and classes.

Contains helper functions for name transformations and other utilities.
"""

from .name import Name, to_snake, to_kebab, to_pascal, to_camel, to_macro_snake, to_macro
from .path import expand_path

__all__ = [
    "Name",
    "to_snake",
    "to_kebab",
    "to_pascal",
    "to_camel",
    "to_macro",
    "to_macro_snake",
    "expand_path",
]
