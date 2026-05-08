"""
desktop_pet.py - A tkinter-based desktop pet player for Codex-style sprite atlases.

Features:
- Transparent, borderless window
- Sprite animation playback from atlas
- Drag to move the pet
- Right-click context menu for state switching and exit
- Pet wanders around the screen edges
- Double-click to toggle state
- Chat-aware mode: reads state file to sync with chat context
- Pixel-art speech bubble for chat messages

Usage:
    python desktop_pet.py --atlas <atlas.png> [--manifest <pet.json>] [--scale 2.0]
    python desktop_pet.py --atlas <atlas.png> --state-file <path>

State file format (JSON, written by the chat agent or pet daemon):
    {
        "state": "running",
        "message": "Processing your request..."
    }
"""

import os
import sys
import json
import argparse
import random
import time
import tkinter as tk
from PIL import Image, ImageTk

FRAME_WIDTH = 192
FRAME_HEIGHT = 208
COLUMNS = 8
DEFAULT_FPS = 10
WANDER_INTERVAL = 5000  # ms between wander actions
WANDER_STEP = 60  # pixels per wander step
STATE_POLL_INTERVAL = 500  # ms between state file checks
AUTO_REVERT_TIMEOUT = 15000  # ms before auto-reverting chat state to idle

# Default state file path
DEFAULT_STATE_FILE = os.path.join(os.path.expanduser("~"), ".workbuddy", "pet_state.json")

# Pixel bubble colors
BUBBLE_BG = "#f8f8f0"     # Off-white (classic pixel UI)
BUBBLE_BORDER = "#3a3a3a"  # Dark gray
BUBBLE_TEXT = "#3a3a3a"    # Dark gray
BUBBLE_PAD_X = 8
BUBBLE_PAD_Y = 4
BUBBLE_ARROW_H = 6         # Arrow/triangle height


class DesktopPet:
    def __init__(self, atlas_path: str, manifest_path: str = None, scale: float = 2.0,
                 state_file: str = None, chat_aware: bool = True, debug_border: bool = False):
        self.scale = scale
        self.frame_w = int(FRAME_WIDTH * scale)
        self.frame_h = int(FRAME_HEIGHT * scale)
        self.debug_border = debug_border
        self.current_state = "idle"
        self.current_frame = 0
        self.dragging = False
        self.drag_offset = (0, 0)
        self.wander_job = None
        self.chat_aware = chat_aware
        self.state_file = state_file or DEFAULT_STATE_FILE
        self.last_state_mtime = 0
        self.last_chat_state = None
        self.auto_revert_job = None  # scheduled auto-revert to idle

        # Load atlas image
        self.atlas = Image.open(atlas_path).convert("RGBA")

        # Load manifest
        self.states = {}
        if manifest_path and os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            for s in manifest.get("states", []):
                self.states[s["name"]] = {
                    "row": s["row"],
                    "frames": s["frames"],
                    "fps": s.get("fps", DEFAULT_FPS),
                }
        else:
            default_names = [
                "idle", "running-right", "running-left", "waving",
                "jumping", "failed", "waiting", "running", "review",
            ]
            for i, name in enumerate(default_names):
                self.states[name] = {"row": i, "frames": 8, "fps": DEFAULT_FPS}

        # === Create root window FIRST (required before PhotoImage) ===
        self.root = tk.Tk()
        self.root.title("Desktop Pet")
        self.root.overrideredirect(True)  # No title bar
        self.root.attributes("-topmost", True)

        # Transparent background (Windows)
        try:
            self.root.wm_attributes("-transparentcolor", "white")
        except Exception:
            pass

        # Main frame to hold pet
        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.pack()

        # Debug border to show actual window bounds
        if self.debug_border:
            self.main_frame.config(highlightbackground="#FF00FF", highlightthickness=2)

        # Canvas for displaying the pet
        self.canvas = tk.Canvas(
            self.main_frame,
            width=self.frame_w,
            height=self.frame_h,
            bg="white",
            highlightthickness=0,
        )
        self.canvas.pack()

        # Tooltip window for chat state messages (separate top-level to avoid
        # being clipped by the transparent-color of the main window)
        self.tooltip_win = tk.Toplevel(self.root)
        self.tooltip_win.overrideredirect(True)
        self.tooltip_win.attributes("-topmost", True)
        try:
            self.tooltip_win.wm_attributes("-transparentcolor", "white")
        except Exception:
            pass

        # Bubble canvas (drawn pixel-art style)
        self.bubble_canvas = tk.Canvas(
            self.tooltip_win,
            bg="white",
            highlightthickness=0,
        )
        self.bubble_canvas.pack()
        self.tooltip_visible = False
        self._bubble_width = 0
        self._bubble_height = 0
        # Start hidden
        self.tooltip_win.withdraw()

        # Map unknown chat states to known animation states
        self.state_aliases = {
            "thinking": "waiting",
            "coding": "running",
            "debugging": "failed",
            "reading": "review",
            "writing": "running",
            "searching": "running-right",
        }

        # Image item on canvas
        self.photo_item = self.canvas.create_image(0, 0, anchor="nw")

        # === Now pre-cache frames (requires root window) ===
        self.photo_frames = {}
        self._precache_frames()

        # Bind events
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._show_menu)

        # State name Chinese labels
        self.state_labels = {
            "idle": "待机",
            "running-right": "向右跑",
            "running-left": "向左跑",
            "waving": "挥手",
            "jumping": "跳跃",
            "failed": "失败",
            "waiting": "等待",
            "running": "工作中",
            "review": "审查代码",
        }

        # Context menu
        self.menu = tk.Menu(self.root, tearoff=0)
        for state_name in self.states:
            label = self.state_labels.get(state_name, state_name)
            self.menu.add_command(
                label=f"状态: {label}",
                command=lambda s=state_name: self.set_state(s),
            )
        self.menu.add_separator()
        self.menu.add_command(label="随机漫游", command=self._start_wander)
        self.menu.add_command(label="停止漫游", command=self._stop_wander)
        self.menu.add_separator()

        # Chat-aware toggle
        self.chat_aware_var = tk.BooleanVar(value=self.chat_aware)
        self.menu.add_checkbutton(
            label="聊天感知模式",
            variable=self.chat_aware_var,
            command=self._toggle_chat_aware,
        )
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self._quit)

        # Position pet at bottom-right of screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        start_x = screen_w - self.frame_w - 50
        start_y = screen_h - self.frame_h - 50
        self.root.geometry(f"+{start_x}+{start_y}")

        # Initialize state file
        if self.chat_aware:
            self._init_state_file()

        # Start animation
        self._animate()

        # Start chat-aware polling
        if self.chat_aware:
            self._poll_chat_state()

        # Auto-wander only if not chat-aware
        if not self.chat_aware:
            self._start_wander()

    def _init_state_file(self):
        """Create the state file directory and initial state."""
        state_dir = os.path.dirname(self.state_file)
        os.makedirs(state_dir, exist_ok=True)
        if not os.path.exists(self.state_file):
            self._write_state_file("idle", "")

    def _write_state_file(self, state: str, message: str = ""):
        """Write current state to the state file."""
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump({
                    "state": state,
                    "message": message,
                    "timestamp": time.time(),
                }, f, indent=2)
        except Exception:
            pass

    def _poll_chat_state(self):
        """Poll the state file for chat-driven state changes."""
        try:
            if os.path.exists(self.state_file):
                mtime = os.path.getmtime(self.state_file)
                if mtime > self.last_state_mtime:
                    self.last_state_mtime = mtime
                    with open(self.state_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    new_state = data.get("state", "idle")
                    message = data.get("message", "")

                    # Map aliased/unknown states to known animation states
                    anim_state = self.state_aliases.get(new_state, new_state)

                    if new_state != self.last_chat_state:
                        self.last_chat_state = new_state
                        if anim_state != "idle":
                            self._stop_wander()
                        self.set_state(anim_state)

                        if message:
                            self._show_tooltip(message)
                        else:
                            self._hide_tooltip()

                        # Schedule auto-revert for non-idle chat states
                        if new_state != "idle":
                            self._schedule_auto_revert()
                        else:
                            self._cancel_auto_revert()
        except Exception:
            pass

        self.root.after(STATE_POLL_INTERVAL, self._poll_chat_state)

    def _draw_pixel_bubble(self, text: str):
        """Draw a pixel-art style speech bubble on the bubble canvas."""
        self.bubble_canvas.delete("all")

        if not text:
            self._bubble_width = 0
            self._bubble_height = 0
            return

        font = ("Courier New", 10, "bold")
        line_h = 15

        # Measure actual text width by creating a temporary text item
        lines = text.split("\n")
        max_line_w = 0
        for line in lines:
            tid = self.bubble_canvas.create_text(0, 0, text=line, font=font, anchor="nw")
            bbox = self.bubble_canvas.bbox(tid)
            self.bubble_canvas.delete(tid)
            if bbox:
                max_line_w = max(max_line_w, bbox[2] - bbox[0])

        num_lines = len(lines)
        bw = max(max_line_w + BUBBLE_PAD_X * 2 + 4, 40)
        bh = num_lines * line_h + BUBBLE_PAD_Y * 2 + BUBBLE_ARROW_H + 4

        # Pixel-art border: draw stepped outline
        # Outer dark border
        self.bubble_canvas.create_rectangle(0, 0, bw, bh - BUBBLE_ARROW_H,
                                             fill=BUBBLE_BG, outline="")
        # Draw pixel-notch corners (simulate pixel art)
        notch = 3  # corner notch size in pixels
        # Top-left notch
        self.bubble_canvas.create_rectangle(0, 0, notch, notch, fill="white", outline="")
        # Top-right notch
        self.bubble_canvas.create_rectangle(bw - notch, 0, bw, notch, fill="white", outline="")
        # Bottom-left notch (above arrow)
        self.bubble_canvas.create_rectangle(0, bh - BUBBLE_ARROW_H - notch, notch, bh - BUBBLE_ARROW_H,
                                             fill="white", outline="")
        # Bottom-right notch
        self.bubble_canvas.create_rectangle(bw - notch, bh - BUBBLE_ARROW_H - notch,
                                             bw, bh - BUBBLE_ARROW_H, fill="white", outline="")

        # Draw border lines (pixel-style: 2px thick)
        # Top
        self.bubble_canvas.create_line(notch, 1, bw - notch, 1, fill=BUBBLE_BORDER, width=2)
        # Bottom
        self.bubble_canvas.create_line(notch, bh - BUBBLE_ARROW_H - 1,
                                        bw - notch, bh - BUBBLE_ARROW_H - 1,
                                        fill=BUBBLE_BORDER, width=2)
        # Left
        self.bubble_canvas.create_line(1, notch, 1, bh - BUBBLE_ARROW_H - notch,
                                        fill=BUBBLE_BORDER, width=2)
        # Right
        self.bubble_canvas.create_line(bw - 1, notch, bw - 1, bh - BUBBLE_ARROW_H - notch,
                                        fill=BUBBLE_BORDER, width=2)

        # Arrow/triangle pointing down at bottom-center
        ax = bw // 2
        arrow_points = [
            ax - 5, bh - BUBBLE_ARROW_H,
            ax + 5, bh - BUBBLE_ARROW_H,
            ax, bh,
        ]
        self.bubble_canvas.create_polygon(arrow_points, fill=BUBBLE_BG, outline=BUBBLE_BORDER, width=1)

        # Draw text
        for i, line in enumerate(text.split("\n")):
            y = BUBBLE_PAD_Y + 2 + i * line_h
            self.bubble_canvas.create_text(
                bw // 2, y,
                text=line,
                font=font,
                fill=BUBBLE_TEXT,
                anchor="n",
            )

        self._bubble_width = bw
        self._bubble_height = bh
        self.bubble_canvas.config(width=bw, height=bh)

    def _show_tooltip(self, text: str = None):
        """Show pixel bubble above the pet."""
        msg = text or ""
        if not msg.strip():
            return

        self._draw_pixel_bubble(msg)

        # Position above pet, centered
        pet_x = self.root.winfo_x()
        pet_y = self.root.winfo_y()
        offset_x = (self.frame_w - self._bubble_width) // 2 if self._bubble_width < self.frame_w else -20
        self.tooltip_win.geometry(f"+{pet_x + offset_x}+{pet_y - self._bubble_height + 2}")
        self.tooltip_win.deiconify()
        self.tooltip_visible = True

    def _hide_tooltip(self):
        """Hide the pixel bubble."""
        if self.tooltip_visible:
            self.tooltip_win.withdraw()
            self.tooltip_visible = False

    def _schedule_auto_revert(self):
        """Schedule auto-revert to idle after timeout (safety net)."""
        self._cancel_auto_revert()
        self.auto_revert_job = self.root.after(AUTO_REVERT_TIMEOUT, self._auto_revert_to_idle)

    def _cancel_auto_revert(self):
        """Cancel pending auto-revert."""
        if self.auto_revert_job:
            self.root.after_cancel(self.auto_revert_job)
            self.auto_revert_job = None

    def _auto_revert_to_idle(self):
        """Auto-revert pet to idle state (called by timeout)."""
        self.auto_revert_job = None
        self.set_state("idle")
        self._hide_tooltip()
        self._write_state_file("idle", "")

    def _toggle_chat_aware(self):
        """Toggle chat-aware mode."""
        self.chat_aware = self.chat_aware_var.get()
        if self.chat_aware:
            self._init_state_file()
            self._poll_chat_state()
            self._stop_wander()
        else:
            self._start_wander()

    def _precache_frames(self):
        """Pre-extract and cache all frames as PhotoImages."""
        for state_name, state_info in self.states.items():
            row = state_info["row"]
            num_frames = state_info["frames"]
            self.photo_frames[state_name] = []
            for col in range(num_frames):
                x1 = col * FRAME_WIDTH
                y1 = row * FRAME_HEIGHT
                x2 = x1 + FRAME_WIDTH
                y2 = y1 + FRAME_HEIGHT
                frame = self.atlas.crop((x1, y1, x2, y2))
                frame = frame.resize((self.frame_w, self.frame_h), Image.LANCZOS)

                datas = list(frame.get_flattened_data())
                new_data = []
                for item in datas:
                    if len(item) == 4 and item[3] > 0:
                        if item[0] > 240 and item[1] > 240 and item[2] > 240:
                            new_data.append((255, 255, 255, 0))
                        else:
                            new_data.append(item)
                    else:
                        new_data.append(item)
                frame.putdata(new_data)

                photo = ImageTk.PhotoImage(frame)
                self.photo_frames[state_name].append(photo)

    def _animate(self):
        """Animate the current state's frames."""
        state = self.states.get(self.current_state)
        if not state:
            return

        frames = self.photo_frames.get(self.current_state, [])
        if not frames:
            return

        self.current_frame = self.current_frame % len(frames)
        self.canvas.itemconfig(self.photo_item, image=frames[self.current_frame])
        self.current_frame += 1

        fps = state.get("fps", DEFAULT_FPS)
        delay = int(1000 / fps)
        self.root.after(delay, self._animate)

    def set_state(self, state_name: str):
        """Switch to a different animation state."""
        if state_name in self.states:
            self.current_state = state_name
            self.current_frame = 0

    def _on_press(self, event):
        """Start dragging the pet."""
        self.dragging = True
        # Convert event coordinates to root coordinates
        widget = event.widget
        x_root = widget.winfo_rootx() + event.x
        y_root = widget.winfo_rooty() + event.y
        self.drag_offset = (x_root - self.root.winfo_x(), y_root - self.root.winfo_y())

    def _on_drag(self, event):
        """Move the pet while dragging."""
        if self.dragging:
            widget = event.widget
            x_root = widget.winfo_rootx() + event.x
            y_root = widget.winfo_rooty() + event.y
            x = x_root - self.drag_offset[0]
            y = y_root - self.drag_offset[1]
            self.root.geometry(f"+{x}+{y}")
            # Move tooltip along with pet
            if self.tooltip_visible:
                offset_x = (self.frame_w - self._bubble_width) // 2 if self._bubble_width < self.frame_w else -20
                self.tooltip_win.geometry(f"+{x + offset_x}+{y - self._bubble_height + 2}")

    def _on_release(self, event):
        """Stop dragging."""
        self.dragging = False

    def _on_double_click(self, event):
        """Double-click to cycle through states."""
        state_names = list(self.states.keys())
        current_idx = state_names.index(self.current_state) if self.current_state in state_names else 0
        next_idx = (current_idx + 1) % len(state_names)
        self.set_state(state_names[next_idx])

    def _show_menu(self, event):
        """Show right-click context menu."""
        self.menu.tk_popup(event.x_root, event.y_root)

    def _start_wander(self):
        """Start random wandering."""
        if self.wander_job:
            return

        def wander():
            if self.dragging:
                self.wander_job = self.root.after(WANDER_INTERVAL, wander)
                return

            action = random.choice(["idle", "move_right", "move_left", "jump", "wave"])

            if action == "idle":
                self.set_state("idle")
            elif action == "move_right":
                self._move_pet(WANDER_STEP, 0)
                self.set_state("running-right")
            elif action == "move_left":
                self._move_pet(-WANDER_STEP, 0)
                self.set_state("running-left")
            elif action == "jump":
                self.set_state("jumping")
            elif action == "wave":
                self.set_state("waving")

            if action != "idle":
                self.root.after(2000, lambda: self.set_state("idle") if not self.dragging else None)

            self.wander_job = self.root.after(WANDER_INTERVAL, wander)

        self.wander_job = self.root.after(WANDER_INTERVAL, wander)

    def _stop_wander(self):
        """Stop wandering."""
        if self.wander_job:
            self.root.after_cancel(self.wander_job)
            self.wander_job = None

    def _move_pet(self, dx: int, dy: int):
        """Move the pet window by dx, dy pixels."""
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max(0, min(x, screen_w - self.frame_w))
        y = max(0, min(y, screen_h - self.frame_h - 30))

        self.root.geometry(f"+{x}+{y}")

    def _quit(self):
        """Exit the pet."""
        self._stop_wander()
        self._hide_tooltip()
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
        except Exception:
            pass
        try:
            self.tooltip_win.destroy()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        """Start the pet application."""
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Desktop Pet Player")
    parser.add_argument("--atlas", required=True, help="Path to sprite atlas PNG")
    parser.add_argument("--manifest", default=None, help="Path to pet.json manifest")
    parser.add_argument("--scale", type=float, default=2.0, help="Display scale factor")
    parser.add_argument("--state-file", default=None, help="Path to chat state JSON file")
    parser.add_argument("--no-chat-aware", action="store_true", help="Disable chat-aware mode")
    parser.add_argument("--debug-border", action="store_true", help="Show magenta border around pet window for debugging")
    args = parser.parse_args()

    if not os.path.exists(args.atlas):
        print(f"ERROR: Atlas not found: {args.atlas}")
        sys.exit(1)

    pet = DesktopPet(
        args.atlas,
        args.manifest,
        args.scale,
        state_file=args.state_file,
        chat_aware=not args.no_chat_aware,
        debug_border=args.debug_border,
    )
    pet.run()


if __name__ == "__main__":
    main()
