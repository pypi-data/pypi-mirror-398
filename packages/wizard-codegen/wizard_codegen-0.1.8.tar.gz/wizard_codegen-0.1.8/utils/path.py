"""
Path utility functions.

Contains helpers for path expansion and resolution.
"""
from __future__ import annotations
from pathlib import Path
import os


def expand_path(path_str: str, *, mkdir: bool = False) -> Path:
    """
    Expand environment variables and ~ in a path string.

    Supports:
    - Environment variables: $VAR, ${VAR}
    - Home directory: ~, ~/path

    Args:
        path_str: Path string that may contain variables
        mkdir: If True, create the directory (and parents) if it doesn't exist

    Returns:
        Path object with variables expanded
    """
    expanded = os.path.expandvars(path_str)  # $VAR, ${VAR}
    expanded = os.path.expanduser(expanded)   # ~
    path = Path(expanded)
    if mkdir:
        path.mkdir(parents=True, exist_ok=True)
    return path
