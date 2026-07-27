"""PyInstaller entry point for the standalone ``skillspector-quality`` binary.

A frozen build has no console-script shim, so it needs a real module to start from. This
mirrors what the ``skillspector-quality`` entry point in ``pyproject.toml`` does.
"""

from __future__ import annotations

import multiprocessing

from skillspector_quality.cli import app

if __name__ == "__main__":
    # Required before anything else in a frozen build: without it, any library that spawns a
    # process re-executes the bundled binary from the top and forks endlessly.
    multiprocessing.freeze_support()
    app()
