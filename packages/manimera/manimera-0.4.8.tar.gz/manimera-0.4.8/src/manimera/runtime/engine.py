"""
Manimera Render Module.

This module provides the `ManimeraRender` class, which handles the instantiation
and rendering of Manim scenes. It integrates with the `ActiveSceneManager` to
automatically detect the scene to render if none is explicitly provided.
"""

# ============================================================
# IMPORTS
# ============================================================

import os
from manim import Scene

from .manager import SCENE_MANAGER
from .settings import SETTINGS, Quality
from ..terminal.banner import Banner
from ..terminal.monitor import MONITOR
from .. import __version__

# ============================================================
# STUDIO RENDER CLASS
# ============================================================


class ManimeraRender:
    """
    Wrapper class to render a Manim Scene.

    This class simplifies the rendering process by automatically resolving
    the active scene from the `ActiveSceneManager` if not provided.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self, scene: Scene = None, clear=True):
        """
        Initialize the renderer and execute the render loop.

        If a scene class is provided, it is instantiated and rendered.
        Otherwise, the active scene is retrieved from the `ActiveSceneManager`.

        Args:
            scene (Scene, optional): The scene class to render. Defaults to None.
        """
        if clear:
            os.system("clear") if os.name == "posix" else os.system("cls")

        if not SETTINGS._banner_shown:
            Banner(
                library_name="Manimera",
                library_version=__version__,
                subtext="Mathematical visualization made simple by Senan",
            )
            SETTINGS._banner_shown = True

        if scene is None:
            scene = SCENE_MANAGER.get_active()

        if scene is None:
            MONITOR.set_termination_reason("No Active Scenes Detected.", "red", "✖")
            exit()

        # Ensure a default quality is set before Scene initialization
        SETTINGS.ensure_quality(Quality.PREMIUM)

        # Print Settings (Ensures we print the latest configuration)
        SETTINGS.print_settings()

        try:
            video = scene()
            video.render()

        except Exception as e:
            MONITOR.set_termination_reason(str(e), "red", "✖")
            raise e
