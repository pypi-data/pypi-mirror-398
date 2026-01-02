# ============================================================
# IMPORTS
# ============================================================

from manim import *
from ..components.clock import Clock

# ============================================================
# SET TIME ANIMATION
# ============================================================


class AdvanceClockTime(Animation):
    """
    Animate a Clock from its current time to a target time.

    This animation smoothly transitions the clock hands from the current time
    to the specified end time, accounting for full minute rotations and day
    rollover. If the end time is earlier than the start time, it assumes the
    next day (24-hour wrap-around).

    Args:
        clock (Clock): The Clock mobject to animate.
        end_time (tuple): Target time as (hour, minute) in 24-hour format.
        **kwargs: Additional animation parameters (rate_func, run_time, etc.).

    Example:
        >>> clock = Clock()
        >>> self.play(AdvanceClockTime(clock, (15, 30)))  # Animate to 3:30 PM
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self, clock: Clock, end_time: tuple, **kwargs):
        """
        Initialize the AdvanceClockTime animation.

        Args:
            clock (Clock): The Clock mobject to animate.
            end_time (tuple): Target time as (hour, minute) in 24-hour format.
            **kwargs: Additional animation parameters.
        """
        super().__init__(clock, **kwargs)

        self.clock = clock
        self.end_time = end_time

        # Get start and end time components
        sh, sm = self.clock.hour, self.clock.minute
        eh, em = end_time

        # Convert times to total minutes since midnight
        self.start_total = sh * 60 + sm
        self.end_total = eh * 60 + em

        # Handle day rollover: if end time is earlier, assume next day
        if self.end_total <= self.start_total:
            self.end_total += 24 * 60

        # Cache initial hand positions for interpolation
        self.initial_minute = clock.minute_hand.copy()
        self.initial_hour = clock.hour_hand.copy()

    # ========================================================
    # ANIMATION METHODS
    # ========================================================

    def interpolate_mobject(self, alpha):
        """
        Interpolate the clock hands based on the animation progress.

        Args:
            alpha (float): Animation progress from 0 to 1.
        """
        # Apply rate function for easing
        eased = self.rate_func(alpha)

        # Calculate current total minutes based on progress
        total_minutes = interpolate(
            self.start_total,
            self.end_total,
            eased,
        )

        # Compute delta from start time
        delta_minutes = total_minutes - self.start_total

        # Calculate rotation angles for hands
        # Minute hand: full rotation every 60 minutes
        minute_angle = -TAU * (delta_minutes / 60)
        # Hour hand: full rotation every 720 minutes (12 hours)
        hour_angle = -TAU * (delta_minutes / 720)

        # Get clock center for rotation
        center = self.clock.frame.get_center()

        # Reset hands to initial positions
        self.clock.minute_hand.become(self.initial_minute)
        self.clock.hour_hand.become(self.initial_hour)

        # Apply rotation to hands
        self.clock.minute_hand.rotate(minute_angle, about_point=center)
        self.clock.hour_hand.rotate(hour_angle, about_point=center)

    def finish(self):
        """
        Finalize the animation by updating the clock's internal time state.

        Returns:
            Animation: The completed animation.
        """
        # Update clock's internal time to match the final state
        self.clock.hour = self.end_time[0]
        self.clock.minute = self.end_time[1]
        return super().finish()
