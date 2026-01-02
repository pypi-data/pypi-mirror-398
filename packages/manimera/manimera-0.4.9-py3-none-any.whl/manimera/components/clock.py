# ============================================================
# IMPORTS
# ============================================================

from manim import *
from typing import Optional, Tuple

# ============================================================
# CLOCK CLASS
# ============================================================


class Clock(VGroup):
    """
    A reusable analog clock construct for Manim scenes.

    This class builds a clock face consisting of:
    - An outer circular frame
    - Tick marks for minutes and hours
    - Optional hour numbers (1–12)
    - Hour and minute hands
    - A central pin

    The clock can be set to a specific time using `set_time`.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        radius=2,
        clock_color=WHITE,
        hand_color=YELLOW,
        show_numbers=True,
        base_color="#1e1e1e",
        stroke=5,
        scale=1,
    ):
        super().__init__()

        # User-configurable options
        self.radius = radius * scale
        self.clock_color = clock_color
        self.hand_color = hand_color
        self.base_color = base_color
        self.show_numbers = show_numbers
        self.stroke = stroke * scale

        # Internal constants
        self.tick_length = 0.1 * scale
        self.number_offset = 0.35 * scale

        # Clock hands (initialized later)
        self.minute_hand: Optional[Line] = None
        self.hour_hand: Optional[Line] = None

        # Clock frame elements
        self.frame: Optional[Circle] = None
        self.ticks: Optional[VGroup] = None

        # Stored time values
        self.hour: int = None
        self.minute: int = None

        # Build the clock components
        self.__create()

    # ========================================================
    # PRIVATE METHODS
    # ========================================================

    def __create(self):
        """Create and assemble all clock components."""

        # Create outer frame and tick marks
        self.frame = self.__create_frame()
        self.ticks = self.__create_ticks()

        # Add frame and ticks to the group
        self.add(self.frame, self.ticks)

        # Optionally add hour numbers
        if self.show_numbers:
            numbers = self.__create_numbers()
            self.add(numbers)

        # Create and add clock hands
        self.minute_hand, self.hour_hand = self.__create_hands()
        self.add(self.minute_hand, self.hour_hand)

        # Create and add the center pin
        pin = self.__create_pin()
        self.add(pin)

        # Set Default Time
        self.set_time(0, 0)

    def __create_frame(self):
        """Create the circular clock frame."""
        return Circle(
            radius=self.radius,
            color=self.base_color,
            stroke_color=self.clock_color,
            stroke_width=self.stroke,
        ).rotate(PI / 2)

    def __create_numbers(self) -> VGroup:
        """Create hour numbers (1–12) positioned around the clock."""
        numbers = VGroup()

        # Place each number evenly around the circle
        for i in range(1, 13):
            angle = TAU * i / 12

            # Create the number text
            num = Tex(str(i), color=self.clock_color).scale_to_fit_height(
                self.radius / 10
            )

            # Start at the top, then rotate into position
            num.move_to((self.radius - self.number_offset) * UP)
            num.rotate(-angle, about_point=ORIGIN).rotate(angle)

            numbers.add(num)

        return numbers

    def __create_ticks(self):
        """Create minute and hour tick marks around the clock face."""
        ticks = VGroup()

        # Create 60 ticks (one for each minute)
        for i in range(0, 60):
            angle = TAU * i / 60

            # Base stroke width for ticks
            width = self.stroke * 0.4

            # Make hour ticks thicker
            if i % 5 == 0:
                width *= 2

            # Draw a single tick mark
            line = Line(
                ORIGIN,
                DOWN * self.tick_length,
                stroke_width=width,
                color=self.clock_color,
            )

            # Position the tick at the clock edge
            line.shift(self.radius * UP)
            line.rotate(-angle, about_point=ORIGIN)

            ticks.add(line)

        return ticks

    def __create_hands(self):
        """Create the hour and minute hands."""

        # Minute hand (longer and thinner)
        minute = Line(
            ORIGIN,
            self.radius * 0.7 * UP,
            stroke_width=self.stroke * 0.8,
            color=self.hand_color,
        )

        # Hour hand (shorter and thicker)
        hour = Line(
            ORIGIN,
            self.radius * 0.4 * UP,
            stroke_width=self.stroke * 1.2,
            color=self.hand_color,
        )

        return minute, hour

    def __create_pin(self):
        """Create the small center pin covering the hand joints."""
        return Dot(radius=self.stroke / 100, color=self.hand_color)

    # ========================================================
    # PUBLIC METHODS
    # ========================================================

    def set_time(self, hour: float, minute: float):
        """
        Set the clock hands to a specific time.

        Args:
            hour (float): Hour value in 24-hour format (0–23).
            minute (float): Minute value (0–59).
        """

        # Validate input ranges
        assert minute >= 0 and minute < 60
        assert hour >= 0 and hour < 24

        # Store the time
        self.hour = hour
        self.minute = minute

        # Calculate rotation angles
        minute_angle = -TAU * minute / 60
        hour_angle = -TAU * hour / 12 + (-TAU / 12) * minute / 60

        # Rotate hands about the clock center
        self.minute_hand.rotate(minute_angle, about_point=self.frame.get_center())
        self.hour_hand.rotate(hour_angle, about_point=self.frame.get_center())

    def get_time(self) -> Tuple[float, float]:
        """
        Get the current time on the clock.

        Returns:
            Tuple[float, float]: The current hour and minute.
        """
        return (self.hour, self.minute)
