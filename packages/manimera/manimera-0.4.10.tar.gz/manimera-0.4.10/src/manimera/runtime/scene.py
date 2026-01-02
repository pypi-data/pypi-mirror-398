"""
Manimera Base Scene Module.

This module defines the `ManimeraScene` class, which serves as the base class
for all scenes in the Manimera library. It provides common functionality
such as watermarking and abstract methods for scene creation.
"""

# ============================================================
# IMPORTS
# ============================================================

from abc import ABC, abstractmethod
from manim import *

from .manager import SCENE_MANAGER
from .settings import SETTINGS
from ..terminal.monitor import MONITOR

# ============================================================
# MANIMERA SCENE BASE CLASS
# ============================================================


class ManimeraScene(Scene, ABC):
    """
    Base class for all Manimera scenes.

    Inherits from `manim.Scene` and `abc.ABC`. This class enforces a structure
    where the scene content is defined in the `create` method, and the `construct`
    method handles the setup (e.g., adding a watermark) and execution.
    """

    # ========================================================
    # PRIVATE HELPERS
    # ========================================================

    def __watermark(self, name="Senan"):
        """
        Create a watermark Mobject.

        Args:
            name (str, optional): The text to display in the watermark. Defaults to "Senan".

        Returns:
            Mobject: A configured Tex object positioned at the bottom-left corner.
        """
        return (
            Tex(name)
            .scale_to_fit_height(0.15)
            .to_corner(DL)
            .set_color(WHITE)
            .shift(DL * 0.3)
        )

    # ========================================================
    # ABSTRACT METHODS
    # ========================================================

    @abstractmethod
    def create(self) -> None:
        """
        Define the scene content.

        This abstract method must be implemented by subclasses to define the
        animations and objects that make up the scene.
        """
        ...

    # ========================================================
    # CONSTRUCT
    # ========================================================

    def __init_subclass__(cls, **kwargs):
        """
        Register the subclass with the ActiveSceneManager.

        This method is called when a class inherits from `ManimeraScene`.
        It automatically registers the new scene class as the active scene.
        """
        super().__init_subclass__(**kwargs)
        SCENE_MANAGER.set_active(cls)

    # ========================================================
    # CONSTRUCT
    # ========================================================

    def construct(self) -> None:
        """
        Execute the scene construction logic.

        This is the entry point for Manim to render the scene. It adds the
        watermark and then calls the `create` method implemented by the subclass.
        """

        # Add Watermark
        self.add(self.__watermark("Senan"))

        # Create content from child class
        try:
            self.create()
        except Exception as e:
            MONITOR.set_termination_reason(f"Failed: {e}", "red", "✖")
            raise e
