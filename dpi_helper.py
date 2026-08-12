#!/usr/bin/env python3
"""
High-DPI support for Windows

Tkinter processes are DPI-unaware by default, so on a display scaled to
125%/150%/200% Windows draws the window at 96 DPI and then bitmap-stretches
the result - which is why everything looks soft. Declaring awareness turns
that stretching off, after which the app has to size itself, because Tk
still lays out in raw pixels.
"""

import sys

# Every pixel measurement in this app was picked on a 96 DPI (100%) display.
BASE_DPI = 96.0

_scale = 1.0


def enable_dpi_awareness():
    """Declare this process DPI-aware. Must run before any window exists.

    Windows locks a process's awareness in at its first window, so calling
    this after Tk() silently does nothing.

    System-level rather than per-monitor is deliberate: these windows are
    fixed-size and sized once at startup, so if one is dragged to a monitor
    with a different scale we want Windows to stretch it rather than leave
    it crisp but the wrong size.
    """
    if sys.platform != "win32":
        return

    import ctypes

    # Windows 8.1+
    try:
        PROCESS_SYSTEM_DPI_AWARE = 1
        if ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_SYSTEM_DPI_AWARE) == 0:
            return
    except (AttributeError, OSError):
        pass

    # Windows Vista+
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


def _query_dpi(root):
    """Real DPI of the display, now that the process is DPI-aware."""
    if sys.platform == "win32":
        try:
            import ctypes
            dpi = ctypes.windll.user32.GetDpiForWindow(root.winfo_id())
            if dpi:
                return float(dpi)
        except (AttributeError, OSError, ValueError):
            pass
    try:
        return float(root.winfo_fpixels("1i"))
    except Exception:
        return BASE_DPI


def init_scaling(root):
    """Match Tk's own scaling to the display DPI. Returns the scale factor.

    Call before building any widgets: Tk resolves a tuple-specified font
    into a concrete size when the widget is created, so widgets built
    beforehand keep the old scaling.
    """
    global _scale

    dpi = _query_dpi(root)
    _scale = dpi / BASE_DPI
    # Pixels per point, which is how Tk converts point-sized fonts. Every
    # font in this app is given in points, so they all follow from this.
    root.tk.call("tk", "scaling", dpi / 72.0)
    return _scale


def get_scale():
    """Current scale factor (1.0 at 100%, 1.5 at 150%, ...)."""
    return _scale


def scale(value):
    """Scale a measurement that was chosen at 96 DPI."""
    return int(round(value * _scale))


def size_window(win, base_width, base_height, fit_content=True):
    """Size *win* from its 96-DPI design size, then centre it on screen.

    Pass None for either dimension to take it straight from the content.
    A design size that is taller than its content leaves a dead band of
    empty window below the last widget, since these layouts pin their
    rows to the top.

    With fit_content a given design size acts as a minimum: fonts grow at
    150% too, and rounding can leave a fixed window a few pixels short,
    which clips the bottom row of controls. Sizes are also capped to the
    screen, since a tall dialog at 200% can end up taller than the display.
    """
    win.update_idletasks()

    width = win.winfo_reqwidth() if base_width is None else scale(base_width)
    height = win.winfo_reqheight() if base_height is None else scale(base_height)
    if fit_content:
        width = max(width, win.winfo_reqwidth())
        height = max(height, win.winfo_reqheight())

    # Leave room for the taskbar and title bar instead of filling the screen.
    width = min(width, win.winfo_screenwidth() - scale(40))
    height = min(height, win.winfo_screenheight() - scale(80))

    x = (win.winfo_screenwidth() - width) // 2
    y = (win.winfo_screenheight() - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")
    return width, height
