"""Utility functions for Vicoa CLI."""

from __future__ import annotations

import os
from pathlib import Path


def get_project_path(path: str | None = None) -> str:
    """Format a project path to use ~ for home directory.

    This creates a more readable path representation by replacing the home
    directory prefix with ~, consistent with how paths are displayed across
    agent instances.

    Args:
        path: The path to format. If None, uses current working directory.

    Returns:
        The formatted path with ~ replacing home directory if applicable.

    Examples:
        >>> format_project_path("/Users/john/projects/myapp")
        "~/projects/myapp"
        >>> format_project_path("/opt/app")
        "/opt/app"
    """
    project_path = os.path.abspath(path) if path else os.getcwd()
    home_dir = str(Path.home())

    if project_path.startswith(home_dir):
        return "~" + project_path[len(home_dir) :]

    return project_path
