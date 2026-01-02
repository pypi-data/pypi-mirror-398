# ============================================================
# IMPORTS
# ============================================================

from manim import *
from typing import Optional, Tuple

# ============================================================
# CLOCK CLASS
# ============================================================


class AnatomicalEye(VGroup):
    """
    A reusable anatomical eye construct for Manim scenes.

    This class builds an anatomical eye consisting of:
    - An outer circular frame
    - A pupil
    - A iris
    - A central pin
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        radius: float = 1.0,
        direction: str = "right",
        eye_color: ManimColor = BLUE,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.radius = radius
        self.direction = direction
        self.eye_color = eye_color

        self._build_eye()
        self.move_to(ORIGIN)

    # ========================================================
    # PRIVATE METHODS
    # ========================================================

    def _build_eye(self):
        """Orchestrate the construction of the anatomical eye."""
        base, ellipse = self._build_base()
        lens = self._build_lens(ellipse)
        iris = self._build_iris(ellipse, lens)
        retina = self._build_retina()

        self.add(base, lens, iris, retina)
        self._apply_direction()

    def _build_base(self) -> Tuple[Union, Ellipse]:
        """
        Build the base structure of the eye.

        Returns:
            Tuple[Union, Ellipse]: The base union shape and the ellipse component.
        """
        circle = Circle(radius=self.radius)
        ellipse = Ellipse(width=self.radius * 0.75, height=self.radius)
        ellipse.move_to(circle.get_edge_center(RIGHT)).shift(LEFT * self.radius / 6)
        base = Union(circle, ellipse)
        return base, ellipse

    def _build_lens(self, ellipse: Ellipse) -> Ellipse:
        """
        Build the lens component of the eye.

        Args:
            ellipse (Ellipse): The ellipse component from the base structure.

        Returns:
            Ellipse: The lens shape.
        """
        lens = Ellipse(
            width=self.radius * 0.4,
            height=self.radius,
            fill_opacity=1,
            fill_color=WHITE,
            stroke_width=0,
        ).scale(0.75)
        lens.move_to(ellipse.get_center())
        return lens

    def _build_iris(self, ellipse: Ellipse, lens: Ellipse) -> Difference:
        """
        Build the iris component of the eye.

        Args:
            ellipse (Ellipse): The ellipse component from the base structure.
            lens (Ellipse): The lens shape to subtract from the iris.

        Returns:
            Difference: The iris shape created by subtracting the lens.
        """
        iris = Ellipse(
            width=self.radius * 0.5,
            height=self.radius,
            fill_opacity=1,
            fill_color=self.eye_color,
            stroke_width=0,
        ).scale(0.75)
        iris.move_to(ellipse.get_center()).shift(RIGHT * self.radius * 0.08)
        iris = (
            Difference(iris, lens)
            .set_color(self.eye_color)
            .set_opacity(1)
            .set_stroke(width=0)
        ).shift(RIGHT * self.radius * 0.04)
        return iris

    def _build_retina(self) -> Arc:
        """
        Build the retina arc component of the eye.

        Returns:
            Arc: The retina arc shape.
        """
        retina = Arc(
            radius=self.radius * 0.85,
            start_angle=2 * PI / 3,
            angle=5 * PI / 6,
            color=YELLOW_A,
            fill_opacity=0,
        )
        return retina

    def _apply_direction(self):
        """Apply the direction flip if needed."""
        if self.direction != "right":
            self.flip(UP)
