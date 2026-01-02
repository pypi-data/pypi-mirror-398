"""
Manimera CLI Entry Point.

This module parses command-line arguments and dispatches control to the
appropriate command handlers in the `cli` package.
"""

# ============================================================
# IMPORTS
# ============================================================

import sys
import argparse
from rich.console import Console

# Import Controllers
from .project import init_project, list_structure
from .chapter import add_chapter
from .scene import add_scene
from .workflow import clean_project, clean_cache, finalize_video

# Import Monitor to disable it for CLI
from ..terminal.monitor import MONITOR

# ============================================================
# MAIN EXECUTION
# ============================================================


def main():
    """Run the Manimera CLI."""
    # Disable monitor output for CLI commands
    MONITOR.disable()

    parser = argparse.ArgumentParser(
        prog="manimera",
        description="Manimera Command Line Interface",
        epilog="Mathematical visualization made simple by Senan.",
    )

    # ========================================================
    # SUBCOMMANDS
    # ========================================================

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ========================================================
    # PROJECT COMMANDS
    # ========================================================

    # Init
    init_parser = subparsers.add_parser(
        "init", help="Initialize a new Manimera project"
    )
    init_parser.add_argument("name", help="Name of the project directory")

    # List
    subparsers.add_parser("list", help="List project structure")

    # Clean
    subparsers.add_parser("clean", help="Clean export and cache directories")

    # Cache
    subparsers.add_parser("cache", help="Clean cache directories")

    # Finalize
    subparsers.add_parser("finalize", help="Move latest video/image to final folder")
    # Alias 'mv' for finalize
    subparsers.add_parser("mv", help="Alias for finalize")

    # ========================================================
    # ADD COMMANDS (Simplified)
    # ========================================================

    # Add subcommand group
    add_parser = subparsers.add_parser("add", help="Add chapters or scenes")
    add_subparsers = add_parser.add_subparsers(dest="add_type", help="What to add")

    # Add Chapter
    chapter_parser = add_subparsers.add_parser("chapter", help="Add a new chapter")
    chapter_parser.add_argument("name", help="Name of the chapter")

    # Add Scene
    scene_parser = add_subparsers.add_parser("scene", help="Add a new scene")
    scene_parser.add_argument("name", help="Name of the scene class (CamelCase)")
    scene_parser.add_argument(
        "chapter",
        nargs="?",
        type=int,
        default=None,
        help="Chapter number (required if not inside a chapter directory)",
    )

    # Parse
    args = parser.parse_args()

    # ========================================================
    # DISPATCH
    # ========================================================

    if args.command == "init":
        init_project(args.name)
    elif args.command == "list":
        list_structure()
    elif args.command == "clean":
        clean_project()
    elif args.command == "cache":
        clean_cache()
    elif args.command in ["finalize", "mv"]:
        finalize_video()
    elif args.command == "add":
        if args.add_type == "chapter":
            add_chapter(args.name)
        elif args.add_type == "scene":
            add_scene(args.name, args.chapter)
        else:
            # No sub-type specified
            add_parser.print_help()
    else:
        # If no arguments, print help
        parser.print_help()


if __name__ == "__main__":
    main()
