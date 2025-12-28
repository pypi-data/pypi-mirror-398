#!/usr/bin/env python3
"""A TUI app to find and delete Python virtual environments."""

import os
import shutil
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Checkbox, Footer, Header, Label, Static


SEARCH_DIRS = [
    Path("/Users/ajayn/Projects"),
    Path("/Users/ajayn/PycharmProjects"),
]
VENV_NAMES = {".venv", "venv"}


def find_venvs() -> list[Path]:
    """Find all virtual environments in the search directories."""
    venvs = []
    for search_dir in SEARCH_DIRS:
        if not search_dir.exists():
            continue
        for root, dirs, _ in os.walk(search_dir):
            root_path = Path(root)
            for venv_name in VENV_NAMES:
                venv_path = root_path / venv_name
                if venv_path.is_dir() and is_venv(venv_path):
                    venvs.append(venv_path)
                    if venv_name in dirs:
                        dirs.remove(venv_name)
    return sorted(venvs)


def is_venv(path: Path) -> bool:
    """Check if a directory is a Python virtual environment."""
    pyvenv_cfg = path / "pyvenv.cfg"
    bin_python = path / "bin" / "python"
    scripts_python = path / "Scripts" / "python.exe"
    return pyvenv_cfg.exists() or bin_python.exists() or scripts_python.exists()


def get_dir_size(path: Path) -> int:
    """Get the total size of a directory in bytes."""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except (PermissionError, OSError):
        pass
    return total


def format_size(size: int) -> str:
    """Format size in bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


class VenvItem(Static):
    """A widget representing a single venv."""

    def __init__(self, venv_path: Path) -> None:
        super().__init__()
        self.venv_path = venv_path
        self.venv_size = get_dir_size(venv_path)

    def compose(self) -> ComposeResult:
        with Horizontal(classes="venv-row"):
            yield Checkbox(id=f"cb-{hash(self.venv_path)}")
            yield Label(f"{self.venv_path}", classes="venv-path")
            yield Label(f"({format_size(self.venv_size)})", classes="venv-size")


class VenvCleanerApp(App):
    """A Textual app to find and delete Python virtual environments."""

    CSS = """
    Screen {
        background: $surface;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        color: $text;
        padding: 1;
    }
    
    #status {
        text-align: center;
        color: $text-muted;
        padding: 1;
    }
    
    .venv-row {
        height: 3;
        padding: 0 1;
        align: left middle;
    }
    
    .venv-path {
        width: 1fr;
        padding-left: 1;
    }
    
    .venv-size {
        width: auto;
        color: $text-muted;
        padding-right: 1;
    }
    
    #venv-list {
        height: 1fr;
        border: solid $primary;
        margin: 1 2;
    }
    
    #buttons {
        height: auto;
        align: center middle;
        padding: 1;
    }
    
    Button {
        margin: 0 1;
    }
    
    #delete-btn {
        background: $error;
    }
    
    #no-venvs {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "select_all", "Select All"),
        ("n", "select_none", "Select None"),
        ("d", "delete_selected", "Delete Selected"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.venvs: list[Path] = []
        self.venv_items: dict[int, VenvItem] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("🐍 Python Virtual Environment Cleaner", id="title")
        yield Label("Scanning for virtual environments...", id="status")
        yield VerticalScroll(id="venv-list")
        with Horizontal(id="buttons"):
            yield Button("Select All", id="select-all-btn", variant="default")
            yield Button("Select None", id="select-none-btn", variant="default")
            yield Button("Delete Selected", id="delete-btn", variant="error")
            yield Button("Refresh", id="refresh-btn", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.scan_venvs()

    def scan_venvs(self) -> None:
        """Scan for virtual environments and populate the list."""
        self.venvs = find_venvs()
        venv_list = self.query_one("#venv-list", VerticalScroll)
        venv_list.remove_children()
        self.venv_items.clear()

        if not self.venvs:
            venv_list.mount(Label("No virtual environments found.", id="no-venvs"))
            self.query_one("#status", Label).update("No virtual environments found.")
            return

        total_size = 0
        for venv_path in self.venvs:
            item = VenvItem(venv_path)
            self.venv_items[hash(venv_path)] = item
            venv_list.mount(item)
            total_size += item.venv_size

        self.query_one("#status", Label).update(
            f"Found {len(self.venvs)} virtual environment(s) - Total: {format_size(total_size)}"
        )

    def get_selected_venvs(self) -> list[Path]:
        """Get all selected virtual environments."""
        selected = []
        for path_hash, item in self.venv_items.items():
            checkbox = item.query_one(Checkbox)
            if checkbox.value:
                selected.append(item.venv_path)
        return selected

    def action_select_all(self) -> None:
        for item in self.venv_items.values():
            item.query_one(Checkbox).value = True

    def action_select_none(self) -> None:
        for item in self.venv_items.values():
            item.query_one(Checkbox).value = False

    def action_delete_selected(self) -> None:
        self.delete_selected()

    def delete_selected(self) -> None:
        """Delete all selected virtual environments."""
        selected = self.get_selected_venvs()
        if not selected:
            self.notify("No virtual environments selected.", severity="warning")
            return

        deleted = 0
        freed = 0
        for venv_path in selected:
            try:
                size = get_dir_size(venv_path)
                shutil.rmtree(venv_path)
                deleted += 1
                freed += size
            except (PermissionError, OSError) as e:
                self.notify(f"Failed to delete {venv_path}: {e}", severity="error")

        self.notify(
            f"Deleted {deleted} venv(s), freed {format_size(freed)}",
            severity="information",
        )
        self.scan_venvs()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select-all-btn":
            self.action_select_all()
        elif event.button.id == "select-none-btn":
            self.action_select_none()
        elif event.button.id == "delete-btn":
            self.delete_selected()
        elif event.button.id == "refresh-btn":
            self.scan_venvs()


if __name__ == "__main__":
    app = VenvCleanerApp()
    app.run()
