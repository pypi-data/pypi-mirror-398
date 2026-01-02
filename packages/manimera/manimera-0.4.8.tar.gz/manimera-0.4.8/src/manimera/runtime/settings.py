"""
Manimera Settings Module.

This module manages the configuration and settings for Manimera renders.
It defines render profiles (Quality), handles Manim configuration updates,
and provides a singleton `Settings` class to manage these states.
"""

# ============================================================
# IMPORTS
# ============================================================

import os
import re
import ast
import inspect
import tempfile

from enum import Enum
from manim import config
from typing import Dict
from typing import Final
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from ..theme import BACKGROUND_GREY
from ..terminal.ui import print_render_settings
from ..terminal.monitor import MONITOR

# ============================================================
# QUALITY
# ============================================================


class Quality(Enum):
    """
    Enumeration for render quality levels.
    """
    MINIMAL = "minimal"
    STANDARD = "standard"
    PREMIUM = "premium"


# ============================================================
# PROFILE CLASS
# ============================================================


@dataclass(frozen=True)
class RenderProfile:
    """
    Data class representing a render profile configuration.

    Attributes:
        width (int): The pixel width of the render.
        height (int): The pixel height of the render.
        fps (int): The frames per second of the render.
    """
    width: int
    height: int
    fps: int


# ============================================================
# PROFILES
# ============================================================

PROFILES: Final[Dict[Quality, RenderProfile]] = {
    Quality.MINIMAL: RenderProfile(1280, 720, 15),
    Quality.STANDARD: RenderProfile(1920, 1080, 30),
    Quality.PREMIUM: RenderProfile(3840, 2160, 60),
}

# ============================================================
# SETTINGS CLASS
# ============================================================


class Settings:
    """
    Singleton class to manage Manim render settings.

    This class handles the application of render profiles, configuration of
    output directories and filenames, and logging of current settings.
    """

    # ========================================================
    # SINGLETON IMPLEMENTATION
    # ========================================================

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self, profiles: Dict[Quality, RenderProfile] = PROFILES):
        """
        Initialize the Settings instance.

        Args:
            profiles (Dict[Quality, RenderProfile], optional): A dictionary mapping
                Quality enums to RenderProfile instances. Defaults to PROFILES.
        """
        self.profiles = profiles
        self._quality_set = False
        self._banner_shown = False

    # ========================================================
    # PRIVATE HELPERS
    # ========================================================

    def _set_width(self, pixel_width: int = 1920):
        """Set the pixel width in Manim config."""
        config.pixel_width = pixel_width

    def _set_height(self, pixel_height: int = 1080):
        """Set the pixel height in Manim config."""
        config.pixel_height = pixel_height

    def _set_frame_rate(self, fps: int = 60):
        """Set the frame rate in Manim config."""
        config.frame_rate = fps

    def _set_background(self, color: str = BACKGROUND_GREY):
        """Set the background color in Manim config."""
        config.background_color = color

    def _set_caller_file(self, profile: RenderProfile):
        """
        Determine the caller file and set the output file path.

        This method inspects the stack to find the file that initiated the render,
        creates an export directory based on the resolution, and sets the
        output filename with a timestamp.

        Args:
            profile (RenderProfile): The render profile being used.

        Raises:
            RuntimeError: If the call stack cannot be inspected.
        """
        try:
            # Resolve caller file
            frame = inspect.stack()[-1]
            caller_file = frame.filename
        except IndexError as e:
            raise RuntimeError("Unable to inspect call stack") from e

        caller_dir = os.path.dirname(os.path.abspath(caller_file))

        # Resolve scene name
        scene_name = self._get_last_scene_instance(caller_file)
        
        # Convert to snake_case for filename
        snake_name = re.sub(r'(?<!^)(?=[A-Z])', '_', scene_name).lower()

        # Resolution string
        resolution = f"{profile.width}x{profile.height}"
        
        # Structure: export/{SCENE_NAME}/{RESOLUTION}/
        export_dir = os.path.join(caller_dir, "export", scene_name, resolution)
        os.makedirs(export_dir, exist_ok=True)

        # Sorted, human-readable timestamp: YYYY-MM-DD_HH-MM-SS
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Filename: snake_name-timestamp
        filename = f"{snake_name}-{timestamp}"

        config.output_file = os.path.join(export_dir, filename)

    def _set_caching(self, value=False):
        """Enable or disable caching in Manim config."""
        config.disable_caching = not value

    def _get_last_scene_instance(self, caller_file) -> str:
        """
        Parse the caller file to find the last defined Scene class.

        Args:
            caller_file (str): Path to the file to parse.

        Returns:
            str: The name of the last class inheriting from ManimeraScene.

        Raises:
            ValueError: If no suitable Scene class is found.
        """
        with open(caller_file, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        # Search from bottom -> top of the file
        for node in reversed(tree.body):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    # Works for Scene and StudioScene
                    if isinstance(base, ast.Name) and base.id in {
                        "ManimeraScene",
                    }:
                        return node.name
        
        MONITOR.set_termination_reason(f"No ManimeraScene class found in file: {Path(caller_file).name}.", "red", "✖")
        exit()

    def _set_temp_media_dir(self, name: str = "manimera_media"):
        """
        Configure a temporary directory for media output.

        Args:
            name (str, optional): Name of the temp directory. Defaults to "manimera_media".
        """
        base_temp = tempfile.gettempdir()
        media_dir = os.path.join(base_temp, name)

        os.makedirs(media_dir, exist_ok=True)
        config.media_dir = media_dir

    # ========================================================
    # PUBLIC INTERFACE
    # ========================================================

    def print_settings(self):
        """
        Print the currently applied render settings to the terminal.
        """
        # If set_quality hasn't been called, we can't print meaningful profile info 
        # unless we track the 'current_level'. Let's assume set_quality sets it.
        if not hasattr(self, "_current_level") or not hasattr(self, "_current_profile"):
             return

        print_render_settings(
            self._current_level.name, 
            self._current_profile, 
            config, 
            config.output_file
        )

    def ensure_quality(self, level: Quality, caching: bool = True):
        """
        Ensure a quality level is set. If already set, this does nothing.
        
        Args:
             level (Quality): Default quality level to apply if none set.
             caching (bool): Default caching setting.
        """
        if not self._quality_set:
            self.set_quality(level, caching)

    def set_quality(self, level: Quality, caching: bool = True):
        """
        Sets render quality according to a preset profile.

        Applies the resolution, frame rate, and other settings defined in the
        selected quality profile. Also configures output paths and logging.

        Args:
            level (Quality): The quality level to apply (MINIMAL, STANDARD, PREMIUM).
            caching (bool, optional): Whether to enable caching. Defaults to True.
        """
        self._quality_set = True
        profile = self.profiles[level]
        
        # Store for printing later
        self._current_level = level
        self._current_profile = profile

        self._set_caching(caching)
        self._set_width(profile.width)
        self._set_height(profile.height)
        self._set_frame_rate(profile.fps)
        self._set_background(BACKGROUND_GREY)

        # Generate filename using render profile
        self._set_caller_file(profile)

        # Temp media directory with constant name
        self._set_temp_media_dir()


SETTINGS = Settings()
