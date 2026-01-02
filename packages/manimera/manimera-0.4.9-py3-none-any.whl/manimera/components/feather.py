# ============================================================
# IMPORTS
# ============================================================

from manim import *
from typing import Optional

# ============================================================
# FEATHER CLASS
# ============================================================


class Feather(VGroup):
    """
    A reusable feather construct for Manim scenes.

    Builds a feather face consisting of:
    - Spine (rachis)
    - Barbs (Bezier curves)
    """

    def __init__(
        self,
        length: float = 6.0,
        barbs: int = 100,
        max_barb_length: float = 0.5,
        curvature: float = 0.4,
        spine_stroke_width: float = 4.0,
        barb_stroke_width: float = 1.0,
        base_offset=0.1,
        barb_color=WHITE,
        spine_color=WHITE,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.length = length
        self.barbs = barbs
        self.max_barb_length = max_barb_length
        self.curvature = curvature
        self.spine_stroke_width = spine_stroke_width
        self.barb_stroke_width = barb_stroke_width
        self.base_offset = base_offset
        self.barb_color = barb_color
        self.spine_color = spine_color

        self._build_spine()
        self._build_barbs()

    # ========================================================
    # PRIVATE METHODS
    # ========================================================

    def _build_spine(self):
        l = self.length
        c = self.curvature

        self.spine = CubicBezier(
            LEFT * l / 2,
            LEFT * l / 4 + UP * c,
            RIGHT * l / 4 - UP * c,
            RIGHT * l / 2,
        ).set_stroke(width=self.spine_stroke_width, color=self.spine_color)

        self.add(self.spine)

    def _build_barbs(self):
        self.barb_group = VGroup()

        for i in range(self.barbs):
            t_raw = i / (self.barbs - 1)
            t = interpolate(self.base_offset, 1.0, t_raw)
            # Exact attachment point on the spine
            start = self.spine.point_from_proportion(t)

            # Tangent direction (numerical derivative)
            eps = 1e-4
            p1 = self.spine.point_from_proportion(min(t + eps, 1))
            p0 = self.spine.point_from_proportion(max(t - eps, 0))
            tangent = normalize(p1 - p0)

            # Normal direction (rotate tangent by 90°)
            normal = rotate_vector(tangent, PI / 2)

            # Alternate sides
            side = normal if i % 2 == 0 else -normal

            # Natural tapering
            barb_len = self.max_barb_length * np.sin(np.pi * t)

            barb = CubicBezier(
                start,
                start + side * barb_len * 0.3,
                start + side * barb_len * 0.7 + tangent * 0.1,
                start + side * barb_len,
            ).set_stroke(width=self.barb_stroke_width, color=self.barb_color)

            self.barb_group.add(barb)

        self.add(self.barb_group)
