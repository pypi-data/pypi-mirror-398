"""
Manimera Banner Module.

This module provides the `Banner` class, which is responsible for displaying
a stylized welcome message or banner in the terminal when the library is initialized.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.style import Style


class Banner:
    """
    Displays a stylized banner in the terminal.

    This class uses the `rich` library to render a colorful and formatted
    banner containing the library name, version, and a subtext message.
    """

    def __init__(self, library_name: str, library_version: str, subtext: str = ""):
        """
        Initialize the Banner instance and display it immediately.

        Args:
            library_name (str): The name of the library to display.
            library_version (str): The version string of the library.
            subtext (str, optional): A subtitle or tagline to display below the version.
                Defaults to "".
        """
        self.library_name = library_name
        self.library_version = library_version
        self.subtext = subtext
        self.console = Console()

        self._show()

    def _show(self):
        """
        Render and print the banner to the console.

        Constructs the banner using `rich.text.Text` and `rich.panel.Panel`
        components and prints it using the `rich.console.Console`.
        """
        title = Text()
        title.append(
            f"{self.library_name}", style=Style(color="bright_magenta", bold=True)
        )
        title.append(
            f" v{self.library_version}", style=Style(color="bright_yellow", bold=True)
        )

        subtitle = Text(
            f"✨  {self.subtext}  ✨",
            style=Style(color="bright_cyan", italic=True, bold=True),
            justify="center",
        )

        panel = Panel(
            subtitle,
            title=title,
            border_style="bright_magenta",
            padding=(1, 4),
        )
        self.console.print(panel)
