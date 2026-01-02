# ============================================================
# IMPORTS
# ============================================================

from manim import *


# ============================================================
# CLASS FadeReveal
# ============================================================


class FadeReveal(Animation):
    """Fade in while moving from `shift_amount` toward the object's final position."""

    def __init__(self, mobject, direction=DOWN, scale=1, reverse=False, **kwargs):
        super().__init__(mobject, **kwargs)
        self.direction = direction * scale
        self.reverse = reverse
        self.mobject.set_opacity(0)

    def interpolate_submobject(self, submobject, starting_submobject, alpha):
        if self.reverse:
            alpha = 1 - alpha
        eased = self.rate_func(alpha)
        submobject.become(
            starting_submobject.copy()
            .shift(self.direction * (1 - eased))
            .set_opacity(eased)
        )
