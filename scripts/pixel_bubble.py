"""
pixel_bubble.py - Pixel-art speech bubble rendering for the desktop pet.
"""
import tkinter as tk
from pet_constants import BUBBLE_BG, BUBBLE_BORDER, BUBBLE_TEXT, BUBBLE_PAD_X, BUBBLE_PAD_Y, BUBBLE_ARROW_H

TRANSPARENT_COLOR = "#F0F0F2"


class PixelBubble:
    """A pixel-art style speech bubble displayed above the pet."""

    def __init__(self, root: tk.Tk):
        self._root = root
        self._visible = False
        self._width = 0
        self._height = 0

        # Transparent toplevel window
        self._win = tk.Toplevel(root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        try:
            self._win.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except Exception:
            pass

        self._canvas = tk.Canvas(self._win, bg=TRANSPARENT_COLOR, highlightthickness=0)
        self._canvas.pack()
        self._win.withdraw()

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def show(self, text: str, x: int, y: int):
        """Show the bubble with text, positioned at screen coordinates (x, y)."""
        if not text or not text.strip():
            return
        self._draw(text)
        self._win.geometry(f"+{x}+{y}")
        self._win.deiconify()
        self._win.lift()
        self._visible = True

    def move(self, x: int, y: int):
        """Reposition the bubble."""
        if self._visible:
            self._win.geometry(f"+{x}+{y}")

    def hide(self):
        """Hide the bubble."""
        if self._visible:
            self._win.withdraw()
            self._visible = False

    def destroy(self):
        """Clean up the bubble window."""
        try:
            self._win.destroy()
        except Exception:
            pass

    # ── internal drawing ──

    def _draw(self, text: str):
        self._canvas.delete("all")

        font = ("Courier New", 10, "bold")
        line_h = 15

        # Measure text
        lines = text.split("\n")
        max_line_w = 0
        for line in lines:
            tid = self._canvas.create_text(0, 0, text=line, font=font, anchor="nw")
            bbox = self._canvas.bbox(tid)
            self._canvas.delete(tid)
            if bbox:
                max_line_w = max(max_line_w, bbox[2] - bbox[0])

        num_lines = len(lines)
        bw = max(max_line_w + BUBBLE_PAD_X * 2 + 4, 40)
        bh = num_lines * line_h + BUBBLE_PAD_Y * 2 + BUBBLE_ARROW_H + 4

        notch = 3

        # Background
        self._canvas.create_rectangle(0, 0, bw, bh - BUBBLE_ARROW_H,
                                       fill=BUBBLE_BG, outline="")

        # Pixel-notch corners (fake transparency)
        for (nx, ny) in [(0, 0), (bw - notch, 0),
                          (0, bh - BUBBLE_ARROW_H - notch),
                          (bw - notch, bh - BUBBLE_ARROW_H - notch)]:
            self._canvas.create_rectangle(nx, ny, nx + notch, ny + notch,
                                           fill=TRANSPARENT_COLOR, outline="")

        # Border (2px)
        bt = 1
        bb = bh - BUBBLE_ARROW_H - 1
        self._canvas.create_line(notch, bt, bw - notch, bt, fill=BUBBLE_BORDER, width=2)
        self._canvas.create_line(notch, bb, bw - notch, bb, fill=BUBBLE_BORDER, width=2)
        self._canvas.create_line(bt, notch, bt, bb - notch, fill=BUBBLE_BORDER, width=2)
        self._canvas.create_line(bw - 1, notch, bw - 1, bb - notch, fill=BUBBLE_BORDER, width=2)

        # Arrow
        ax = bw // 2
        self._canvas.create_polygon(
            ax - 5, bh - BUBBLE_ARROW_H,
            ax + 5, bh - BUBBLE_ARROW_H,
            ax, bh,
            fill=BUBBLE_BG, outline=BUBBLE_BORDER, width=1,
        )

        # Text
        for i, line in enumerate(lines):
            y = BUBBLE_PAD_Y + 2 + i * line_h
            self._canvas.create_text(bw // 2, y, text=line, font=font,
                                      fill=BUBBLE_TEXT, anchor="n")

        self._width = bw
        self._height = bh
        self._canvas.config(width=bw, height=bh)
