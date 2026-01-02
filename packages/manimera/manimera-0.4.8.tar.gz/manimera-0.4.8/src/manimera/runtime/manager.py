"""
Manimera Scene Manager Module.

This module provides the `ActiveSceneManager` class, which is a singleton
responsible for tracking the currently active scene class. This allows for
dynamic scene resolution during runtime.
"""

from typing import Type, Optional


class SceneManager:
    """
    Singleton manager for tracking the currently active scene.

    This class ensures that only one instance exists and provides methods
    to set, get, and clear the active scene class.
    """

    _instance: Optional["SceneManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active_scene = None
        return cls._instance

    def set_active(self, scene_cls: Type) -> None:
        """
        Set the active scene class.

        Args:
            scene_cls (Type): The scene class to mark as active.
        """
        self._active_scene = scene_cls

    def get_active(self) -> Optional[Type]:
        """
        Retrieve the currently active scene class.

        Returns:
            Optional[Type]: The active scene class, or None if no scene is set.
        """
        return self._active_scene

    def clear_active(self) -> None:
        """
        Clear the active scene.

        Resets the active scene to None.
        """
        self._active_scene = None


# Singleton instance
SCENE_MANAGER = SceneManager()
