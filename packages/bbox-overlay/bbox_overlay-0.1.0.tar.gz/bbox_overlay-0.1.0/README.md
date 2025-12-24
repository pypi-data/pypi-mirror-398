# bbox-overlay

Minimal Python overlay to draw bounding boxes on top of the screen (Linux/X11).

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

## CLI options

```bash
bbox-overlay --help
```
