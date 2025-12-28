# cleaner-for-venv

A TUI app to find and delete Python virtual environments.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/cleaner-for-venv.svg)](https://pypi.org/project/cleaner-for-venv/)

## Installation

```bash
pip install cleaner-for-venv
```

## Usage

```bash
venv-cleaner
```

Or run as a module:

```bash
python -m venv_cleaner
```

## Features

- Scans directories for `.venv` and `venv` folders
- Shows size of each virtual environment
- Select multiple venvs with checkboxes
- Bulk delete with one click

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `a` | Select all |
| `n` | Select none |
| `d` | Delete selected |
| `q` | Quit |

## License

MIT
