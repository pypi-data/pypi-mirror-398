"""A TUI app to find and delete Python virtual environments."""

from .app import VenvCleanerApp

__version__ = "0.1.0"


def main() -> None:
    """Entry point for the venv-cleaner CLI."""
    app = VenvCleanerApp()
    app.run()
