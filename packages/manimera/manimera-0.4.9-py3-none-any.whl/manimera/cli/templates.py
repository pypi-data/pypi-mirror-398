"""
CLI Templates Module.

This module contains string templates used by the Manimera CLI to generate
boilerplate code for new projects, scenes, and utility scripts.
"""

# ============================================================
# BOILERPLATE CODE
# ============================================================

DEFAULT_SCENE_TEMPLATE = """from manimera import *

class {class_name}(ManimeraScene):
    def create(self): ...
    

if __name__ == "__main__":
    ManimeraRender()
"""

CLEAN_SCRIPT_TEMPLATE = """import shutil
from pathlib import Path
from rich.console import Console

def clean_dirs(project_root: str, dirnames: list[str], verbose: bool = False):
    \"\"\"Delete all directories matching given names recursively.\"\"\"
    console = Console()
    root = Path(project_root).resolve()
    deleted = 0

    for dirpath in root.rglob("*/"):
        if dirpath.name in dirnames:
            try:
                shutil.rmtree(dirpath)
                if verbose:
                    console.print(f"[green] - {dirpath.relative_to(root)}[/]")
                deleted += 1
            except Exception:
                console.print(f"[red] - {dirpath.relative_to(root)}[/]")

    console.print(f"[bold green]Deleted {deleted} directories[/]")

if __name__ == "__main__":
    clean_dirs(".", ["__pycache__", "export"], verbose=False)
"""
