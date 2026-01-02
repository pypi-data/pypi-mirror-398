"""
CLI Project Management Module.

This module handles the creation and management of Manimera projects.
It includes functionality to initialize a new project structure and
listing existing projects (if applicable within a broader workspace).
"""

# ============================================================
# IMPORTS
# ============================================================

import os
from pathlib import Path
from rich.tree import Tree

from .utils import CONSOLE, print_success, print_error, print_info, get_project_root
from .templates import CLEAN_SCRIPT_TEMPLATE

# ============================================================
# COMMAND HANDLERS
# ============================================================


def init_project(name: str):
    """
    Initialize a new Manimera project.

    Args:
        name (str): The name of the project directory to create.
    """
    can_create = True
    try:
        # Get Project Root
        project_path = get_project_root()
        can_create = False
    except FileNotFoundError:
        ...

    if not can_create:
        print_error("Can not create Manimera project inside another Manimera project.")
        return

    project_path = Path.cwd() / name

    if project_path.exists():
        print_error(f"Directory '{name}' already exists.")

    try:
        # Create Project Root
        project_path.mkdir(parents=True)
        (project_path / ".manimera-project").touch()

        # Create Default Chapter Introduction
        chapter_name = "Chapter-001-Introduction"
        chapter_path = project_path / chapter_name
        chapter_path.mkdir()
        (chapter_path / ".manimera-chapter").touch()
        (chapter_path / "assets").mkdir()
        (chapter_path / "export").mkdir()

        # Create Scripts Directory
        scripts_path = project_path / "scripts"
        scripts_path.mkdir(exist_ok=True)

        # Prepare destination: root/final
        final_dir = project_path / "final"
        final_dir.mkdir(exist_ok=True)

        # Create Clean Script
        clean_script_path = scripts_path / "clean.py"
        with open(clean_script_path, "w", encoding="utf-8") as f:
            f.write(CLEAN_SCRIPT_TEMPLATE)

        print_success(f"Initialized new Manimera project: [bold cyan]{name}[/]")
        print_info(f"Navigate to it with: [yellow]cd {name}[/]")

    except Exception as e:
        print_error(f"Failed to initialize project: {e}")


def list_structure():
    """
    List the structure of the current Manimera project.
    """
    try:
        root = get_project_root()
        tree = Tree(f"[bold cyan]{root.name}[/]")

        # Walk through the directory and add nodes to the tree
        # Simplistic approach: just top level chapters
        chapters = sorted(
            [
                p
                for p in root.iterdir()
                if p.is_dir() and (p / ".manimera-chapter").exists()
            ]
        )

        for chapter in chapters:
            chapter_branch = tree.add(f"[bold green]{chapter.name}[/]")

            # Count scenes
            scenes = list(chapter.glob("*.py"))
            if scenes:
                for scene in scenes:
                    chapter_branch.add(f"[white]{scene.name}[/]")
            else:
                chapter_branch.add("[dim italic]No scenes[/]")

        CONSOLE.print(tree)

    except FileNotFoundError:
        print_error("Not inside a Manimera project.")
