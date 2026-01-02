"""
CLI Utilities Module.

This module provides helper functions for the Manimera CLI, including
methods to find the project root, validate project structure, and
handle rich console output.
"""

# ============================================================
# IMPORTS
# ============================================================

import os
import sys
from pathlib import Path
from rich.console import Console

# ============================================================
# GLOBALS
# ============================================================

CONSOLE = Console()

# ============================================================
# PROJECT RESOLUTION
# ============================================================


def get_project_root(start_path: Path = None) -> Path:
    """
    Find the root of the Manimera project.

    Searches upwards from the given `start_path` (defaults to CWD) for a
    directory containing the `.manimera-project` marker file.

    Args:
        start_path (Path, optional): Directory to start searching from. Defaults to None.

    Returns:
        Path: The absolute path to the project root.

    Raises:
        FileNotFoundError: If the project root is not found.
    """
    if start_path is None:
        start_path = Path.cwd()
    
    current = start_path.resolve()

    # Search for project root up to system root
    for parent in [current] + list(current.parents):
        if (parent / ".manimera-project").exists():
            return parent
    
    raise FileNotFoundError("No Manimera project found. Are you currently inside a project initialized with 'manimera init'?")


def is_inside_chapter(path: Path) -> bool:
    """
    Check if the given path is inside a Manimera chapter.

    Args:
        path (Path): Path to check.

    Returns:
        bool: True if the path contains a '.manimera-chapter' file.
    """
    return (path / ".manimera-chapter").exists()


# ============================================================
# CONSOLE HELPERS
# ============================================================

def print_error(message: str) -> None:
    """Print an error message in red."""
    CONSOLE.print(f"[bold red]Error:[/bold red] {message}")
    sys.exit(1)

def print_success(message: str) -> None:
    """Print a success message in green."""
    CONSOLE.print(f"[bold green]Success:[/bold green] {message}")

def print_info(message: str) -> None:
    """Print an informational message in blue."""
    CONSOLE.print(f"[bold blue]Info:[/bold blue] {message}")
