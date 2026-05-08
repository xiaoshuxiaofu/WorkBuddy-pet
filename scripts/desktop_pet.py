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
- Context usage bar: shows token usage and percentage below the pet

Usage:
    python desktop_pet.py --atlas <atlas.png> [--manifest <pet.json>] [--scale 2.0]
    python desktop_pet.py --atlas <atlas.png> --state-file <path>

State file format (JSON, written by the chat agent):
    {
        "state": "running",
        "message": "Processing your request...",
        "context_used": 85000,
        "context_total": 128000
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

# Context bar colors
CTX_COLOR_LOW = "#4CAF50"      # Green <50%
CTX_COLOR_MEDIUM = "#FF9800"   # Orange 50-80%
CTX_COLOR_HIGH = "#F44336"     # Red >80%
CTX_COLOR_BG = "#E0E0E0"       # Background gray
CTX_BAR_HEIGHT = 8
CTX_TEXT_HEIGHT = 14


class DesktopPet:
    def __init__(self, atlas_path: str, manifest_path: str = None, scale: float = 2.0,
                 state_file: str = None, chat_aware: bool = True):
        self.scale = scale
        self.frame_w = int(FRAME_WIDTH * scale)
        self.frame_h = int(FRAME_HEIGHT * scale)
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
        self.context_used = 0
        self.context_total = 128000

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

        # Main frame to hold pet + context bar
        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.pack()

        # Canvas for displaying the pet
        self.canvas = tk.Canvas(
            self.main_frame,
            width=self.frame_w,
            height=self.frame_h,
            bg="white",
            highlightthickness=0,
        )
        self.canvas.pack()

        # === Context usage bar (below pet) ===
        ctx_frame = tk.Frame(self.main_frame, bg="white", height=CTX_BAR_HEIGHT + CTX_TEXT_HEIGHT + 4)
        ctx_frame.pack(fill="x", padx=4)
        ctx_frame.pack_propagate(False)

        # Progress bar canvas
        bar_width = self.frame_w - 8
        self.ctx_bar_canvas = tk.Canvas(
            ctx_frame,
            width=bar_width,
            height=CTX_BAR_HEIGHT + CTX_TEXT_HEIGHT + 4,
            bg="white",
            highlightthickness=0,
        )
        self.ctx_bar_canvas.pack()

        # Context text
        self.ctx_text_id = self.ctx_bar_canvas.create_text(
            bar_width // 2, 2,
            text="上下文: 0K / 128K (0%)",
            font=("Microsoft YaHei", 8),
            fill="#666666",
            anchor="n",
        )

        # Progress bar background
        bar_y = CTX_TEXT_HEIGHT + 4
        self.ctx_bar_bg = self.ctx_bar_canvas.create_rectangle(
            0, bar_y, bar_width, bar_y + CTX_BAR_HEIGHT,
            fill=CTX_COLOR_BG, outline="",
        )
        # Progress bar fill
        self.ctx_bar_fill = self.ctx_bar_canvas.create_rectangle(
            0, bar_y, 0, bar_y + CTX_BAR_HEIGHT,
            fill=CTX_COLOR_LOW, outline="",
        )
        self.bar_width = bar_width
        self.bar_y = bar_y

        # Tooltip window for chat state messages (separate top-level to avoid
        # being clipped by the transparent-color of the main window)
        self.tooltip_win = tk.Toplevel(self.root)
        self.tooltip_win.overrideredirect(True)
        self.tooltip_win.attributes("-topmost", True)
        # Make the tooltip window itself transparent on white background
        try:
            self.tooltip_win.wm_attributes("-transparentcolor", "white")
        except Exception:
            pass
        self.tooltip_label = tk.Label(
            self.tooltip_win,
            text="",
            bg="#FFFFDD",
            fg="#333333",
            font=("Microsoft YaHei", 9),
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=3,
            wraplength=200,
        )
        self.tooltip_label.pack()
        self.tooltip_visible = False
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

        # Bind events (bind to main_frame for context bar area too)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._show_menu)
        self.ctx_bar_canvas.bind("<ButtonPress-1>", self._on_press)
        self.ctx_bar_canvas.bind("<B1-Motion>", self._on_drag)
        self.ctx_bar_canvas.bind("<ButtonRelease-1>", self._on_release)
        self.ctx_bar_canvas.bind("<ButtonPress-3>", self._show_menu)

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
        start_y = screen_h - self.frame_h - CTX_BAR_HEIGHT - CTX_TEXT_HEIGHT - 90
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

    def _update_context_bar(self):
        """Update the context usage bar display."""
        if self.context_total <= 0:
            pct = 0
        else:
            pct = min(self.context_used / self.context_total, 1.0)

        # Format text
        used_k = self.context_used / 1000
        total_k = self.context_total / 1000
        pct_str = f"{pct * 100:.1f}%"
        text = f"上下文: {used_k:.0f}K / {total_k:.0f}K ({pct_str})"
        self.ctx_bar_canvas.itemconfig(self.ctx_text_id, text=text)

        # Update bar
        fill_width = int(self.bar_width * pct)
        self.ctx_bar_canvas.coords(
            self.ctx_bar_fill,
            0, self.bar_y, fill_width, self.bar_y + CTX_BAR_HEIGHT,
        )

        # Color based on percentage
        if pct < 0.5:
            color = CTX_COLOR_LOW
        elif pct < 0.8:
            color = CTX_COLOR_MEDIUM
        else:
            color = CTX_COLOR_HIGH
        self.ctx_bar_canvas.itemconfig(self.ctx_bar_fill, fill=color)

        # Also update text color for high usage
        if pct >= 0.8:
            self.ctx_bar_canvas.itemconfig(self.ctx_text_id, fill=CTX_COLOR_HIGH)
        else:
            self.ctx_bar_canvas.itemconfig(self.ctx_text_id, fill="#666666")

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
                    "context_used": self.context_used,
                    "context_total": self.context_total,
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

                    # Update context info
                    ctx_used = data.get("context_used", 0)
                    ctx_total = data.get("context_total", 128000)
                    if ctx_used != self.context_used or ctx_total != self.context_total:
                        self.context_used = ctx_used
                        self.context_total = ctx_total
                        self._update_context_bar()

                    # Map aliased/unknown states to known animation states
                    anim_state = self.state_aliases.get(new_state, new_state)

                    if new_state != self.last_chat_state:
                        self.last_chat_state = new_state
                        if anim_state != "idle":
                            self._stop_wander()
                        self.set_state(anim_state)

                        if message:
                            self.tooltip_label.config(text=message)
                            self._show_tooltip()
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

    def _show_tooltip(self):
        """Show tooltip above the pet."""
        if not self.tooltip_visible and self.tooltip_label.cget("text"):
            # Position the tooltip window above the pet
            pet_x = self.root.winfo_x()
            pet_y = self.root.winfo_y()
            # Wait for the label to update its size, then center it above pet
            self.tooltip_win.update_idletasks()
            tw = self.tooltip_label.winfo_width()
            offset_x = (self.frame_w - tw) // 2
            self.tooltip_win.geometry(f"+{pet_x + offset_x}+{pet_y - 35}")
            self.tooltip_win.deiconify()
            self.tooltip_visible = True

    def _hide_tooltip(self):
        """Hide the tooltip."""
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
                self.tooltip_win.update_idletasks()
                tw = self.tooltip_label.winfo_width()
                offset_x = (self.frame_w - tw) // 2
                self.tooltip_win.geometry(f"+{x + offset_x}+{y - 35}")

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
        y = max(0, min(y, screen_h - self.frame_h))

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
    )
    pet.run()


if __name__ == "__main__":
    main()
