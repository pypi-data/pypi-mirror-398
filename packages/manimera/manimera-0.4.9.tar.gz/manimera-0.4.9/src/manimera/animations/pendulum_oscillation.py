from manim import *


class PendulumOscillation(Animation):
    """
    Oscillate a mobject around a pivot point like a pendulum.
    """

    def __init__(
        self,
        mobject,
        amplitude=20 * DEGREES,
        frequency=1.0,
        damping=0.0,
        phase=0.0,
        **kwargs,
    ):
        super().__init__(mobject, **kwargs)

        self.pivot_point = mobject.get_pivot()
        self.amplitude = amplitude
        self.frequency = frequency
        self.damping = damping
        self.phase = phase

        # Cache initial state to avoid accumulation
        self.start_mobject = mobject.copy()

    def interpolate_mobject(self, alpha):
        # Convert alpha → time
        t = alpha * self.run_time

        # Pendulum angle
        angle = (
            self.amplitude
            * np.sin(2 * np.pi * self.frequency * t + self.phase)
            * np.exp(-self.damping * t)
        )

        # Reset geometry, then rotate
        self.mobject.become(self.start_mobject)
        self.mobject.rotate(angle, about_point=self.pivot_point)
