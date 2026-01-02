# ============================================================
# IMPORTS
# ============================================================

from manim import *


# ============================================================
# PENDULUM CLASS
# ============================================================


class Pendulum(VGroup):
    """
    A reusable pendulum construct for Manim scenes.

    Builds a pendulum consisting of:
    - Bob (Circle)
    - String (Line)
    """

    def __init__(
        self,
        bob_radius=0.5,
        string_length=4,
        bob_color=RED,
        string_color=WHITE,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.bob = Circle(radius=bob_radius, color=bob_color, fill_opacity=1)
        self.string = Line(ORIGIN, UP * string_length, color=string_color)

        self.add(self.string, self.bob)
        self.move_to(ORIGIN)

    # ============================================================
    # GETTERS
    # ============================================================

    def get_bob(self):
        return self.bob

    def get_string(self):
        return self.string

    def get_pivot(self):
        return self.string.get_end()
