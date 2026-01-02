"""
CLI Scene Management Module.

This module handles the creation of new scene files within a chapter,
generating boilerplate code based on `ManimeraScene`.
"""

# ============================================================
# IMPORTS
# ============================================================

import re
from pathlib import Path
from .utils import (
    get_project_root,
    is_inside_chapter,
    print_success,
    print_error,
    print_info,
)
from .templates import DEFAULT_SCENE_TEMPLATE

# ============================================================
# HELPER FUNCTIONS
# ============================================================


def get_available_chapters():
    """
    Get a list of all available chapters in the project.

    Returns:
        list: List of tuples (chapter_number, chapter_path, chapter_name).
              Returns empty list if not in a project or no chapters exist.
    """
    try:
        root = get_project_root()
        chapters = []

        for path in sorted(root.iterdir()):
            if path.is_dir() and (path / ".manimera-chapter").exists():
                # Parse chapter number from "Chapter-NNN-Name" format
                parts = path.name.split("-")
                if len(parts) >= 2 and parts[0] == "Chapter" and parts[1].isdigit():
                    chapter_num = int(parts[1])
                    chapters.append((chapter_num, path, path.name))

        return sorted(chapters, key=lambda x: x[0])
    except FileNotFoundError:
        return []


# ============================================================
# COMMAND HANDLERS
# ============================================================


def add_scene(name: str, chapter_number: int = None):
    """
    Add a new scene to a chapter.

    If run from inside a chapter directory, adds the scene there.
    If run from elsewhere, requires chapter_number to specify target chapter.

    Args:
        name (str): The name of the scene class (CamelCase).
                    The filename will be converted to snake_case.
        chapter_number (int, optional): The chapter number to add the scene to.
                                       Required if not inside a chapter directory.
    """
    current_dir = Path.cwd()
    target_dir = None

    try:
        # Validate Project Root linkage
        root = get_project_root(current_dir)

        # Check if we are inside a chapter directly
        if is_inside_chapter(current_dir):
            if chapter_number is not None:
                print_info(
                    f"Already inside a chapter. Ignoring chapter number {chapter_number}."
                )
            target_dir = current_dir
        else:
            # Not inside a chapter, need chapter_number
            if chapter_number is None:
                chapters = get_available_chapters()
                if not chapters:
                    print_error(
                        "No chapters found in project. Create a chapter first with 'manimera add chapter <name>'."
                    )

                print_error(
                    "Not inside a chapter directory. Please specify a chapter number.\n"
                    f"[bold blue]Available chapters:[/]\n"
                    + "\n".join([f"  [{num:03d}] {name}" for num, _, name in chapters])
                )

            # Find the chapter with the specified number
            chapters = get_available_chapters()
            target_chapter = None

            for num, path, chap_name in chapters:
                if num == chapter_number:
                    target_chapter = path
                    break

            if target_chapter is None:
                chapters_list = "\n".join(
                    [f"  [{num:03d}] {chap_name}" for num, _, chap_name in chapters]
                )
                print_error(
                    f"Chapter {chapter_number:03d} not found.\n"
                    f"[bold blue]Available chapters:[/]\n{chapters_list}"
                )

            target_dir = target_chapter

        # Convert ClassName to snake_case_filename
        class_name = name
        # Regex to convert CamelCase to snake_case
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        snake_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

        filename = f"{snake_name}.py"
        file_path = target_dir / filename

        if file_path.exists():
            print_error(f"Scene file '{filename}' already exists in {target_dir.name}.")

        # Generate Content
        content = DEFAULT_SCENE_TEMPLATE.format(class_name=class_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print_success(
            f"Created scene [bold cyan]{class_name}[/] in [yellow]{target_dir.name}/{filename}[/]"
        )

    except FileNotFoundError:
        print_error("Not inside a Manimera project.")
    except Exception as e:
        print_error(f"Failed to add scene: {e}")
