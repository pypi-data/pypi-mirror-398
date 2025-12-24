import argparse
import json
import re
import sys
import tkinter as tk

from . import __version__
from .overlay import run_overlay


def parse_boxes(raw):
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for --boxes: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("--boxes must be a JSON array")

    boxes = []
    for idx, item in enumerate(data):
        label = None
        if isinstance(item, dict):
            try:
                x = item["x"]
                y = item["y"]
                w = item["w"]
                h = item["h"]
            except KeyError as exc:
                raise ValueError(f"Box {idx} missing key: {exc}") from exc
            label = item.get("label")
        elif isinstance(item, (list, tuple)) and len(item) in (4, 5):
            if len(item) == 4:
                x, y, w, h = item
            else:
                x, y, w, h, label = item
        else:
            raise ValueError(
                f"Box {idx} must be an object with x,y,w,h or a 4/5-item array"
            )

        if label is not None and not isinstance(label, str):
            raise ValueError(f"Box {idx} label must be a string")

        for name, value in (("x", x), ("y", y), ("w", w), ("h", h)):
            if not isinstance(value, (int, float)):
                raise ValueError(f"Box {idx} {name} must be a number")

        if w < 0 or h < 0:
            raise ValueError(f"Box {idx} w/h must be non-negative")

        boxes.append((int(x), int(y), int(w), int(h), label))

    return boxes


_HEX_COLOR_RE = re.compile(r"^[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")


def normalize_color(value):
    value = value.strip()
    if value.startswith("#"):
        return value
    if _HEX_COLOR_RE.fullmatch(value):
        return f"#{value}"
    return value


def validate_color(value):
    normalized = normalize_color(value)
    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        root.winfo_rgb(normalized)
    except tk.TclError as exc:
        raise ValueError(
            "Invalid --color. Use a Tk color name (e.g. 'red') or hex like '#RRGGBB'."
        ) from exc
    finally:
        if root is not None:
            root.destroy()
    return normalized


def build_parser():
    parser = argparse.ArgumentParser(
        description="Draw bounding boxes on a fullscreen overlay (Linux/X11).",
        formatter_class=argparse.RawTextHelpFormatter,
        prog="bbox-overlay",
    )
    parser.add_argument(
        "--boxes",
        required=True,
        help=(
            "JSON array of boxes in xywh; dicts may include label.\n"
            'Example: \'[{"x":10,"y":10,"w":50,"h":40,"label":"cat"}]\''
        ),
    )
    parser.add_argument(
        "--color",
        default="#00ff00",
        help="Outline color (name like 'red' or hex like '#RRGGBB')",
    )
    parser.add_argument("--width", type=int, default=2, help="Outline width in pixels")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Auto-close after N seconds (otherwise waits for any key)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"bbox-overlay {__version__}",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.width < 1:
        parser.error("--width must be >= 1")

    if args.timeout is not None and args.timeout <= 0:
        parser.error("--timeout must be > 0")

    try:
        boxes = parse_boxes(args.boxes)
    except ValueError as exc:
        parser.error(str(exc))

    try:
        color = validate_color(args.color)
    except ValueError as exc:
        parser.error(str(exc))

    if args.timeout is None:
        print("Press any key to close (or Esc).", file=sys.stderr, flush=True)

    run_overlay(
        boxes,
        outline=color,
        width=args.width,
        timeout=args.timeout,
        close_on_stdin=args.timeout is None,
    )


if __name__ == "__main__":
    main()
