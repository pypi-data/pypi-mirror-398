# ============================================================
# IMPORTS
# ============================================================

from manim import *


# ============================================================
# CATHEDRAL LAMP CLASS
# ============================================================


class CathedralLamp(VGroup):
    """
    A stylized hanging cathedral lamp with a glowing light source.
    """

    def __init__(
        self,
        string_length: float = 3,
        lamp_scale: float = 0.25,
        light_scale: float = 1.0,
        intensity=0,
    ):
        super().__init__()

        self.lamp_scale = lamp_scale
        self.light_scale = light_scale
        self.string_length = string_length
        self.hanger = None

        self._build_lamp()
        self.set_intensity(intensity)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_lamp(self):
        width = 3 * self.lamp_scale
        height = 2 * self.lamp_scale

        self.light = self._create_light(width)
        self.lamp_body = self._create_lamp_body(width, height)
        self.decor = self._add_decorative_lines(self.lamp_body)

        top_cap, bottom_cap = self._create_caps(self.lamp_body)
        hanger_dot, string, ceiling_cap = self._create_string(top_cap)
        self.hanger = ceiling_cap
        self.add(
            self.light,
            self.lamp_body,
            self.decor,
            top_cap,
            bottom_cap,
            string,
            hanger_dot,
            ceiling_cap,
        )
        self.move_to(ORIGIN)

    # ------------------------------------------------------------------
    # Components
    # ------------------------------------------------------------------

    def _create_light(self, width):
        return Circle(
            radius=width * self.light_scale,
            color=YELLOW,
            fill_opacity=0.2,
            stroke_width=0,
        )

    def _create_lamp_body(self, width, height):
        return Rectangle(
            width=width,
            height=height,
            color=YELLOW,
            stroke_color=DARK_BROWN,
            stroke_width=10 * self.lamp_scale,
            fill_opacity=1,
        )

    def _create_caps(self, body):
        cap = Triangle(
            color=BLACK,
            fill_opacity=1,
            stroke_width=0,
            stroke_color=DARK_BROWN,
        )
        cap.stretch(2.5 * self.lamp_scale, dim=0)
        cap.stretch(0.5 * self.lamp_scale, dim=1)

        top_cap = cap.copy()
        bottom_cap = cap.copy().flip(RIGHT)

        top_cap.move_to(body.get_edge_center(UP), aligned_edge=DOWN)
        bottom_cap.move_to(body.get_edge_center(DOWN), aligned_edge=UP)

        return top_cap, bottom_cap

    def _create_string(self, top_cap):
        hanger_dot = Dot(
            radius=0.2 * self.lamp_scale,
            color=BLACK,
        ).move_to(top_cap.get_edge_center(UP))

        string = Line(
            hanger_dot.get_center(),
            self.string_length * UP,
            color=DARK_BROWN,
        )

        ceiling_cap = Circle(
            radius=0.3 * self.lamp_scale,
            color=DARK_BROWN,
        ).move_to(string.get_edge_center(UP))

        return hanger_dot, string, ceiling_cap

    # ------------------------------------------------------------------
    # Decorations
    # ------------------------------------------------------------------

    def _add_decorative_lines(self, body):
        stroke = 8 * self.lamp_scale

        lines = VGroup(
            Line(body.get_corner(UL), body.get_edge_center(DOWN)),
            Line(body.get_corner(UR), body.get_edge_center(DOWN)),
            Line(body.get_corner(DL), body.get_edge_center(UP)),
            Line(body.get_corner(DR), body.get_edge_center(UP)),
        )

        for line in lines:
            line.set_color(DARK_BROWN)
            line.set_stroke(width=stroke)

        lines = VGroup(*lines)
        return lines

    def set_intensity(self, alpha=1, light_max_intensity=0.2):
        lamp_color = interpolate_color(GREY, YELLOW, alpha)
        light_intensity = interpolate(0, light_max_intensity, alpha)

        self.lamp_body.set_fill(lamp_color)
        self.light.set_opacity(light_intensity)
        return self

    def get_pivot(self):
        return self.hanger.get_center()
