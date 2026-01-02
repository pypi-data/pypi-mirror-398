# ============================================================
# IMPORTS
# ============================================================

from manim import *

# ============================================================
# NETWORK TOWER CLASS
# ============================================================


class NetworkTower(VGroup):
    """
    Network Tower made from straight lines with a dot on top and signal arcs.

    This class builds a stylized network tower consisting of:
    - A main triangular structure
    - Support cross-bracing
    - An antenna on top
    - Signal waves radiating from the antenna
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        tower_height=4.0,
        tower_width=1.5,
        tower_color=WHITE,
        wave_color=YELLOW,
        levels=3,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # Public configuration
        self.tower_height = tower_height
        self.tower_width = tower_width
        self.tower_color = tower_color
        self.wave_color = wave_color
        self.levels = levels
        self._scale = self.tower_height / 4

        # Initialize key points (will be set in _define_key_points)
        self.bottom_left = None
        self.bottom_right = None
        self.top = None
        self.antenna = None

        self._build_tower()

    # ========================================================
    # PRIVATE METHODS
    # ========================================================

    def _build_tower(self):
        """Orchestrate the construction of the tower."""
        self._define_key_points()
        self._build_main_edges()
        self._build_support_structure()
        self._add_antenna()
        self._add_signal_waves()

        self.move_to(ORIGIN)

    def _define_key_points(self):
        """Define the geometric anchor points of the tower."""
        self.bottom_left = LEFT * (self.tower_width / 2)
        self.bottom_right = RIGHT * (self.tower_width / 2)
        self.top = UP * self.tower_height

    def _build_main_edges(self):
        """Create the two slanted sides of the tower."""
        left_edge = Line(
            self.bottom_left,
            self.top,
            color=self.tower_color,
            stroke_width=8 * self._scale,
        )
        right_edge = Line(
            self.bottom_right,
            self.top,
            color=self.tower_color,
            stroke_width=8 * self._scale,
        )
        self.add(left_edge, right_edge)

    def _build_support_structure(self):
        """Add horizontal bars and diagonal cross bracing."""
        for level in range(self.levels + 1):
            alpha = level / (self.levels + 1)

            left_point = interpolate(self.bottom_left, self.top, alpha)
            right_point = interpolate(self.bottom_right, self.top, alpha)

            # Horizontal bars (skip base)
            if level > 0:
                bar = Line(
                    left_point,
                    right_point,
                    color=self.tower_color,
                    stroke_width=8 * self._scale,
                )
                self.add(bar)

            # Diagonal cross braces
            if level < self.levels:
                next_alpha = (level + 1) / (self.levels + 1)
                next_left = interpolate(self.bottom_left, self.top, next_alpha)
                next_right = interpolate(self.bottom_right, self.top, next_alpha)

                diag_lr = Line(
                    left_point,
                    next_right,
                    color=self.tower_color,
                    stroke_width=8 * self._scale,
                )
                diag_rl = Line(
                    right_point,
                    next_left,
                    color=self.tower_color,
                    stroke_width=8 * self._scale,
                )
                self.add(diag_lr, diag_rl)

    def _add_antenna(self):
        """Add the antenna dot at the top of the tower."""
        self.antenna = Dot(self.top, radius=0.1 * self._scale, color=self.tower_color)
        self.add(self.antenna)

    def _add_signal_waves(self):
        """Add non-intersecting signal arcs above the antenna."""
        wave_group = VGroup()

        # Angle formed by slanted rods (used to avoid intersection)
        tower_spread_angle = self.tower_width / self.tower_height + PI / 4

        arc_start_angle = tower_spread_angle / 2 - PI / 2
        arc_sweep_angle = TAU - tower_spread_angle

        base_radius = 0.5 * self._scale
        radius_step = 0.35 * self._scale
        arc_count = 3

        for i in range(arc_count):
            arc = Arc(
                radius=base_radius + i * radius_step,
                start_angle=arc_start_angle,
                angle=arc_sweep_angle,
                arc_center=self.top,
                color=self.wave_color,
                stroke_width=8 * self._scale,
            )
            wave_group.add(arc)

        self.add(wave_group)
