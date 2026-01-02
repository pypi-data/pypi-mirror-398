# Manimera

**Manimera** is a wrapper around **Manim Community** designed to simplify the creation of mathematical visualizations, with a focus on **production pipelines** and ease of use. It provides an intuitive interface for animating mathematical concepts, graphics, and educational content—perfect for YouTube creators and educators.

This library is developed by **Senan**, creator of educational videos using Manim.

---

## Features

- **Simplified Workflow**: Create Manim animations with minimal boilerplate code.
- **Production Ready**: Designed for efficient rendering pipelines and project management.
- **Fully Documented**: Comprehensive docstrings and type hints for a better development experience.
- **Easy Integration**: Seamlessly integrates with existing Manim projects.
- **Quick Rendering**: optimized settings for fast rendering and exporting.

---

## Installation

You can install Manimera using `pip`:

```bash
pip install manimera
````

Or, if you are using `uv`:

```bash
uv pip install manimera
```

After installation, add Manimera to your project:

```bash
uv add manimera
```

---

## Manimera CLI

Manimera includes a streamlined Command Line Interface (CLI) for creating, organizing, and managing Manim-based animation projects.

### 1. Initialize a Project

Create a new Manimera project with the standard directory structure:

```bash
manimera init MyProject
```

This generates a hierarchy similar to:

* `Chapter-000`, `Chapter-001`, ...

  * `assets/` — Local media files (images, audio, etc.)
  * `export/` — Rendered videos and images
* `scripts/` — Utility and workflow scripts
* Project-level configuration files

---

### 2. Add Chapters & Scenes

Manimera uses a clear `add` command group to create new chapters and scenes with boilerplate code.

#### Add a Chapter

```bash
manimera add chapter Introduction
```

This creates a new chapter directory with the appropriate numbering and structure.

#### Add a Scene

```bash
# Add a scene inside the current chapter
manimera add scene MyFirstScene

# Or explicitly specify a chapter number
manimera add scene MyFirstScene 2
```

* Scene names must be valid CamelCase Python class names.
* The chapter number is required if you are not inside a chapter directory.

---

### 3. Workflow Utilities

Manage build artifacts and finalize your renders easily.

```bash
# Clean cache and export directories
manimera clean

# Move the latest render to the final output directory
manimera finalize

# Alias for finalize
manimera mv
```

The `finalize` command automatically selects the most recent render and applies context-aware naming.

---

### 4. List Project Structure

Display an overview of chapters and scenes in your project:

```bash
manimera list
```

This is useful for quickly inspecting project organization without navigating directories manually.

---

## Quick Start

Here’s a basic example of creating a simple animation:

```python
# ClockCreation.py
from manimera import *

# ClockCreation class
class ClockCreation(ManimeraScene):
    def create(self):
        clock = Clock()
        self.play(Create(clock))

# Entry point
if __name__ == "__main__":
    # This will auto-detect the `ClockCreation` class and render it.
    ManimeraRender() 
```

---

## License

This project is licensed under the **MIT License**.

---

## About

Created by **Senan**, Manimera helps streamline animation production for teaching and learning, making it easier to create engaging educational content.
