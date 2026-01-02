from manim import *


class LampGlow(Animation):
    """
    Animate lamp lighting without storing state on the object.
    """

    def __init__(self, lamp, max_light_opacity=0.2, direction=1, **kwargs):
        super().__init__(lamp, **kwargs)
        self.max_light_opacity = max_light_opacity
        self.direction = direction
        # Cache original geometry to avoid accumulation
        self.start_light = lamp.light.copy()

    def interpolate_mobject(self, alpha):
        alpha = np.clip(alpha, 0, 1)
        if self.direction != 1:
            alpha = 1 - alpha

        eased = self.rate_func(alpha)

        # Lamp body color
        lamp_color = interpolate_color(GREY, YELLOW, eased)
        self.mobject.lamp_body.set_fill(lamp_color, opacity=1)

        # Light glow
        glow_opacity = interpolate(0, self.max_light_opacity, eased)
        self.mobject.light.become(self.start_light)
        self.mobject.light.set_fill(YELLOW, opacity=glow_opacity)
