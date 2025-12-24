import os
import select
import sys
import termios
import tkinter as tk
import tty


def _create_line(root, x, y, w, h, color):
    if w <= 0 or h <= 0:
        return None

    window = tk.Toplevel(root)
    window.overrideredirect(True)
    window.geometry(f"{w}x{h}+{x}+{y}")
    window.configure(bg=color)
    window.attributes("-topmost", True)
    return window


LABEL_BG = "#000000"
LABEL_FG = "#ffffff"


def _build_line_windows(root, boxes, color, thickness):
    windows = []
    for x, y, w, h, _label in boxes:
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        if w <= 0 or h <= 0:
            continue

        t = min(thickness, w, h)
        top = _create_line(root, x, y, w, t, color)
        bottom = _create_line(root, x, y + h - t, w, t, color)
        left = _create_line(root, x, y, t, h, color)
        right = _create_line(root, x + w - t, y, t, h, color)

        for line in (top, bottom, left, right):
            if line is not None:
                windows.append(line)

    return windows


def _create_label(root, text, x, y, fg, bg, screen_w, screen_h):
    window = tk.Toplevel(root)
    window.overrideredirect(True)
    window.configure(bg=bg)
    window.attributes("-topmost", True)

    label = tk.Label(window, text=text, fg=fg, bg=bg, bd=0, padx=4, pady=2)
    label.pack()

    window.update_idletasks()
    w = window.winfo_width()
    h = window.winfo_height()

    label_x = max(0, min(x, screen_w - w))
    label_y = y - h - 2
    if label_y < 0:
        label_y = min(y + 2, screen_h - h)

    window.geometry(f"{w}x{h}+{label_x}+{label_y}")
    return window


def _build_label_windows(root, boxes, fg, bg, screen_w, screen_h):
    windows = []
    for x, y, _w, _h, label in boxes:
        if not label:
            continue
        window = _create_label(root, label, x, y, fg, bg, screen_w, screen_h)
        windows.append(window)
    return windows


def _setup_stdin_poll(root, close_callback):
    if not sys.stdin.isatty():
        return None

    fd = sys.stdin.fileno()
    try:
        original_settings = termios.tcgetattr(fd)
    except termios.error:
        return None

    # Cbreak mode lets us receive single key presses without Enter.
    tty.setcbreak(fd)
    restored = False

    def restore():
        nonlocal restored
        if restored:
            return
        restored = True
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, original_settings)
        except termios.error:
            pass

    def poll():
        if restored:
            return
        try:
            readable, _, _ = select.select([fd], [], [], 0)
        except (OSError, ValueError):
            restore()
            return
        if readable:
            try:
                os.read(fd, 1)
            except OSError:
                restore()
                return
            close_callback()
            return
        root.after(50, poll)

    root.after(50, poll)
    return restore


def run_overlay(
    boxes,
    outline="#00ff00",
    width=2,
    timeout=None,
    close_on_stdin=False,
):
    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry("1x1+0+0")
    root.attributes("-topmost", True)

    try:
        root.attributes("-alpha", 0.0)
    except tk.TclError:
        root.withdraw()

    thickness = max(1, int(width))
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    windows = _build_line_windows(root, boxes, outline, thickness)
    windows.extend(
        _build_label_windows(root, boxes, LABEL_FG, LABEL_BG, screen_w, screen_h)
    )

    def close(_evt=None):
        if stdin_restore is not None:
            stdin_restore()
        for win in windows:
            try:
                win.destroy()
            except tk.TclError:
                pass
        root.destroy()

    stdin_restore = None
    if close_on_stdin:
        stdin_restore = _setup_stdin_poll(root, close)

    root.bind_all("<Escape>", close)
    for win in windows:
        win.bind("<Escape>", close)

    if windows and not close_on_stdin:
        windows[0].focus_force()

    if timeout is not None:
        root.after(int(timeout * 1000), close)

    root.mainloop()
    if stdin_restore is not None:
        stdin_restore()
