"""
CLI Chapter Management Module.

This module provides functionality to add new chapters to an existing
Manimera project, ensuring proper structure and naming conventions.
"""

# ============================================================
# IMPORTS
# ============================================================

from pathlib import Path
from .utils import get_project_root, print_success, print_error, print_info

# ============================================================
# COMMAND HANDLERS
# ============================================================

def add_chapter(name: str):
    """
    Add a new chapter to the current project.

    Args:
        name (str): The name suffix for the chapter (e.g., "Introduction").
                    Will be prefixed with strict numbering if auto-increment is implied,
                    or used as-is if it matches the pattern.
    """
    try:
        root = get_project_root()
        
        # Determine strict naming pattern or custom
        # User requirement: "Chapter-000, Chapter-001..." default logic
        # If user provides "MyChapter", we should auto-number it to "Chapter-NNN-MyChapter"
        
        # Find highest chapter number
        existing_chapters = [p for p in root.iterdir() if p.is_dir() and (p / ".manimera-chapter").exists()]
        max_num = -1
        
        for ch in existing_chapters:
            # Try to parse "Chapter-NNN"
            parts = ch.name.split("-")
            if len(parts) >= 2 and parts[0] == "Chapter" and parts[1].isdigit():
                max_num = max(max_num, int(parts[1]))
                
        next_num = max_num + 1
        new_chapter_name = f"Chapter-{next_num:03d}-{name}"

        chapter_path = root / new_chapter_name

        if chapter_path.exists():
            print_error(f"Chapter directory '{new_chapter_name}' already exists.")

        # Create Structure
        chapter_path.mkdir()
        (chapter_path / ".manimera-chapter").touch()
        (chapter_path / "assets").mkdir()
        (chapter_path / "export").mkdir()

        print_success(f"Created new chapter: [bold cyan]{new_chapter_name}[/]")

    except FileNotFoundError:
        print_error("Not inside a Manimera project. Cannot add chapter.")
    except Exception as e:
        print_error(f"Failed to add chapter: {e}")
