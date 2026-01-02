"""
Manimera Animations Package.

This package provides custom Animation classes for creating complex
visual effects and transitions.
"""

from .advance_clock_time import AdvanceClockTime
from .pendulum_oscillation import PendulumOscillation
from .lamp_glow import LampGlow
from .fade_reveal import FadeReveal

__all__ = [
    "AdvanceClockTime",
    "PendulumOscillation",
    "LampGlow",
    "FadeReveal",
]
