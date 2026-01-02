"""
Manimera Terminal UI Module.

This module provides utility functions for displaying rich, formatted output
to the terminal. It handles the visualization of render settings and other
informational panels using the Rich library.
"""

# ============================================================
# IMPORTS
# ============================================================

from typing import Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# ============================================================
# GLOBALS
# ============================================================

CONSOLE = Console()

# ============================================================
# RENDER OUTPUT
# ============================================================


def print_render_settings(
    profile_name: str, profile_data: Any, config: Any, output_path: str
):
    """
    Prints the current render settings in a Rich panel.

    Constructs a table containing key render configuration details like
    resolution, frame rate, and output paths, wraps it in a styled panel,
    and prints it to the console.

    Args:
        profile_name (str): The name of the quality profile (e.g., 'STANDARD').
        profile_data (RenderProfile): The render profile object containing width, height, and fps.
        config (Any): The global manim configuration object.
        output_path (str): The calculated absolute path to the output file.
    """
    table = Table(show_header=False, box=None)

    # Populate table with settings
    table.add_row("Profile", profile_name)
    table.add_row("Width", f"{profile_data.width} px")
    table.add_row("Height", f"{profile_data.height} px")
    table.add_row("FPS", f"{profile_data.fps}")
    table.add_row("Background", str(config.background_color))
    table.add_row("Caching", str(not config.disable_caching))
    table.add_row("Save Last Frame", str(config.save_last_frame))
    table.add_row("Frame Width", f"{config.frame_width:.2f} units")
    table.add_row("Frame Height", f"{config.frame_height:.2f} units")
    table.add_row("Media Dir", f"{config.media_dir}")
    table.add_row("Output File", f"{output_path}")

    # Create and print the panel
    title = Text("Render Settings", style="bold cyan")
    panel = Panel(table, title=title, border_style="cyan", padding=(1, 2))
    CONSOLE.print(panel)
