"""
CLI Workflow Module.

This module provides automation for common workflow tasks such as cleaning
export directories and finalizing/renaming rendered videos.
"""

# ============================================================
# IMPORTS
# ============================================================

import os
import shutil
import tempfile
from pathlib import Path
from rich.prompt import Confirm

# We can reuse the clean logic from templates or just implement it direct
from .utils import get_project_root, print_success, print_error, print_info, CONSOLE

# ============================================================
# COMMAND HANDLERS
# ============================================================


def clean_cache(name="manimera_media"):
    """
    Remove all data in temporary directories.
    """
    try:
        if not Confirm.ask(
            f"Are you sure you want to clean 'manimera_media' directory cache?"
        ):
            print_info("Operation cancelled.")
            return

        base_temp = tempfile.gettempdir()
        media_dir = os.path.join(base_temp, name)

        if os.path.exists(media_dir):
            shutil.rmtree(media_dir)
            print_success(f"Removed {media_dir}")
        else:
            print_info(f"{media_dir} does not exist.")

    except FileNotFoundError:
        print_error("Not inside a Manimera project.")


def clean_project():
    """
    Remove all '__pycache__' directories entirely,
    and remove contents of 'export' directories without deleting the directory itself.
    """
    try:
        root = get_project_root()

        deleted_pycache = 0
        cleaned_export = 0

        if not Confirm.ask(
            f"Are you sure you want to clean '__pycache__' and contents of 'export' in [cyan]{root.name}[/]?"
        ):
            print_info("Operation cancelled.")
            return

        for dirpath in root.rglob("*"):
            # Remove __pycache__ completely
            if dirpath.is_dir() and dirpath.name == "__pycache__":
                try:
                    shutil.rmtree(dirpath)
                    CONSOLE.print(f"[green] - removed {dirpath.relative_to(root)}[/]")
                    deleted_pycache += 1
                except Exception:
                    CONSOLE.print(f"[red] - failed {dirpath.relative_to(root)}[/]")

            # Clean export directory contents only
            elif dirpath.is_dir() and dirpath.name == "export":
                for item in dirpath.iterdir():
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                    except Exception:
                        CONSOLE.print(f"[red] - failed {item.relative_to(root)}[/]")
                CONSOLE.print(
                    f"[green] - cleaned contents of {dirpath.relative_to(root)}[/]"
                )
                cleaned_export += 1

        print_success(
            f"Removed {deleted_pycache} '__pycache__' directories "
            f"and cleaned {cleaned_export} 'export' directories."
        )

    except FileNotFoundError:
        print_error("Not inside a Manimera project.")


def finalize_video():
    """
    Copy the latest rendered video to the 'final' directory.

    This command searches all chapters in the project for the most recently
    modified video file and copies it to the project's 'final' directory.
    If a video with the same chapter and class name already exists, it will
    be replaced with the new file. Works from anywhere inside the project.
    """
    try:
        root = get_project_root()

        # Find all chapters in the project root
        chapters = [
            p
            for p in root.iterdir()
            if p.is_dir() and (p / ".manimera-chapter").exists()
        ]

        if not chapters:
            print_error("No chapters found in project.")
            return

        # Collect all video files from all chapter export directories
        all_videos = []
        for chapter in chapters:
            export_dir = chapter / "export"
            if export_dir.exists():
                videos = list(export_dir.rglob("*.mp4"))
                all_videos.extend(videos)

        if not all_videos:
            print_error("No rendered videos found in any chapter.")
            return

        # Find the latest video by modification time
        latest_video = max(all_videos, key=os.path.getmtime)

        # Prepare destination: root/final
        final_dir = root / "final"
        final_dir.mkdir(exist_ok=True)

        # Extract information from the video path
        # Expected structure: Chapter-<number>/export/SceneName/Resolution/filename.mp4
        rel_path = latest_video.relative_to(root)
        parts = rel_path.parts

        # Extract chapter name (first part should be Chapter-<number>)
        chapter_name = parts[0] if len(parts) > 0 and "Chapter" in parts[0] else "Ref"

        # Extract scene name (should be after 'export')
        scene_name = "Unknown"
        if len(parts) >= 3 and parts[1] == "export":
            scene_name = parts[2]  # Scene name is typically after export/

        # Extract resolution (parent directory name, usually WxH)
        resolution = latest_video.parent.name

        # Construct new filename: Chapter-SceneName-Resolution.mp4
        new_name = f"{chapter_name}-{scene_name}-{resolution}.mp4"
        dest_path = final_dir / new_name

        # Check if a file with the same chapter and scene name exists
        # Pattern: Chapter-SceneName-*.mp4
        pattern_prefix = f"{chapter_name}-{scene_name}-"
        existing_files = [
            f for f in final_dir.glob("*.mp4") if f.name.startswith(pattern_prefix)
        ]

        # Remove existing files with the same chapter and scene name
        for existing_file in existing_files:
            try:
                existing_file.unlink()
                print_info(f"Removed old version: [dim]{existing_file.name}[/]")
            except Exception as e:
                print_error(f"Failed to remove old file: {e}")

        # Copy the latest video to final directory
        shutil.copy2(latest_video, dest_path)

        print_success(
            f"Finalized video:\n"
            f"  From: [dim]{latest_video.relative_to(root)}[/]\n"
            f"  To:   [bold cyan]{dest_path.relative_to(root)}[/]"
        )

    except FileNotFoundError:
        print_error("Not inside a Manimera project.")
    except Exception as e:
        print_error(f"Failed to finalize video: {e}")
