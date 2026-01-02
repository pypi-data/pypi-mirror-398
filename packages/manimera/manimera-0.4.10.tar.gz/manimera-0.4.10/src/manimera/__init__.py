"""
Manimera Library.

Manimera is a wrapper around Manim Community that provides a simplified
interface for creating mathematical visualizations, with a focus on
production pipelines and ease of use.
"""

# Version
__version__ = "0.4.10"

# Entry Point To Manimera
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)

# External Libraries
from manim import *

# Local Imports
from .terminal import *
from .runtime import *
from .theme import *
from .components import *
from .animations import *
from .constants import *
