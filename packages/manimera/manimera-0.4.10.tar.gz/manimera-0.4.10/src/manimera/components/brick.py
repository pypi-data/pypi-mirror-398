# ============================================================
# IMPORTS
# ============================================================

from manim import *

# ============================================================
# BRICK CLASS
# ============================================================


class Brick(VGroup):
    """
    A reusable brick construct for Manim scenes.

    Builds a brick face consisting of:
    - Front (Rectangle)
    - Top (Polygon)
    - Side (Polygon)
    """

    def __init__(
        self,
        width=3,
        height=1,
        depth=1,
        color=RED,
        brick_stroke_width=1,
        **kwargs,
    ):
        super().__init__(**kwargs)

        front = Rectangle(width=width, height=height)
        top = Polygon(
            front.get_corner(UL),
            front.get_corner(UR),
            front.get_corner(UR) + RIGHT * depth + UP * depth * 0.5,
            front.get_corner(UL) + RIGHT * depth + UP * depth * 0.5,
        )
        side = Polygon(
            front.get_corner(UR),
            front.get_corner(DR),
            front.get_corner(DR) + RIGHT * depth + UP * depth * 0.5,
            front.get_corner(UR) + RIGHT * depth + UP * depth * 0.5,
        )

        self.add(
            top.set_fill(color, 0.9),
            side.set_fill(color, 0.8),
            front.set_fill(color, 1.0),
        )
        stroke_color = interpolate_color(color, BLACK, 0.5)
        self.set_stroke(stroke_color, brick_stroke_width)
