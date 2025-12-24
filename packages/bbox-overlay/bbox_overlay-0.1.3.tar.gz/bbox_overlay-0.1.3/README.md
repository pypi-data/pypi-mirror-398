# bbox-overlay

[![PyPI](https://img.shields.io/pypi/v/bbox-overlay.svg)](https://pypi.org/project/bbox-overlay/)
[![Python](https://img.shields.io/pypi/pyversions/bbox-overlay.svg)](https://pypi.org/project/bbox-overlay/)
[![CI](https://github.com/albertoburgosplaza/bbox-overlay/actions/workflows/ci.yml/badge.svg)](https://github.com/albertoburgosplaza/bbox-overlay/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/bbox-overlay.svg)](https://github.com/albertoburgosplaza/bbox-overlay/blob/main/LICENSE)

Minimal Python overlay to draw bounding boxes on top of the screen (Linux/X11).

## Highlights

- Lightweight X11 overlay using thin border windows.
- Optional labels and color control.
- Simple CLI with JSON input.

![Overlay example](https://raw.githubusercontent.com/albertoburgosplaza/bbox-overlay/main/docs/overlay-example.svg)

## Requirements

- Linux/X11 (or WSLg/XWayland on Windows 11).
- Tkinter (e.g. `sudo apt-get install python3-tk` on Ubuntu).

## Install

### PyPI

```bash
python3 -m pip install bbox-overlay
```

### Editable (dev)

```bash
python3 -m pip install -e .[dev]
```

## Usage

```bash
bbox-overlay --boxes '[{"x":100,"y":100,"w":200,"h":150,"label":"cat"}]'
```

- Close with `Esc`, `Ctrl+C`, or any key in the console (when `--timeout` is omitted).
- Coordinates are pixel-based, origin at top-left.
- The overlay uses thin border windows per box to avoid fullscreen opacity on X11.
- Labels are optional and use the `label` field in each box object.
- Colors accept Tk names (`red`, `cyan`) or hex (`#RRGGBB`).

## Development

```bash
ruff check .
ruff format .
mypy bbox_overlay
pytest
```

## Project links

- Source: https://github.com/albertoburgosplaza/bbox-overlay
- Issues: https://github.com/albertoburgosplaza/bbox-overlay/issues
- Changelog: https://github.com/albertoburgosplaza/bbox-overlay/blob/main/CHANGELOG.md

## CLI options

```bash
bbox-overlay --help
```
