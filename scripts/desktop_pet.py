"""
desktop_pet.py - A tkinter-based desktop pet player for Codex-style sprite atlases.

Features:
- Transparent, borderless window
- Sprite animation playback from atlas
- Drag to move the pet
- Right-click context menu for state switching and exit
- Pet wanders around the screen edges
- Double-click to toggle state

Usage:
    python desktop_pet.py --atlas <atlas.png> [--manifest <pet.json>] [--scale 2.0]
"""

import os
import sys
import json
import argparse
import random
import tkinter as tk
from PIL import Image, ImageTk

FRAME_WIDTH = 192
FRAME_HEIGHT = 208
COLUMNS = 8
DEFAULT_FPS = 10
WANDER_INTERVAL = 5000  # ms between wander actions
WANDER_STEP = 60  # pixels per wander step


class DesktopPet:
    def __init__(self, atlas_path: str, manifest_path: str = None, scale: float = 2.0):
        self.scale = scale
        self.frame_w = int(FRAME_WIDTH * scale)
        self.frame_h = int(FRAME_HEIGHT * scale)
        self.current_state = "idle"
        self.current_frame = 0
        self.dragging = False
        self.drag_offset = (0, 0)
        self.wander_job = None

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
            # Default: 9 states, 8 frames each
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

        # Canvas for displaying the pet
        self.canvas = tk.Canvas(
            self.root,
            width=self.frame_w,
            height=self.frame_h,
            bg="white",
            highlightthickness=0,
        )
        self.canvas.pack()

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

        # Context menu
        self.menu = tk.Menu(self.root, tearoff=0)
        for state_name in self.states:
            self.menu.add_command(
                label=f"State: {state_name}",
                command=lambda s=state_name: self.set_state(s),
            )
        self.menu.add_separator()
        self.menu.add_command(label="Random Wander", command=self._start_wander)
        self.menu.add_command(label="Stop Wander", command=self._stop_wander)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self._quit)

        # Position pet at bottom-right of screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        start_x = screen_w - self.frame_w - 50
        start_y = screen_h - self.frame_h - 80
        self.root.geometry(f"+{start_x}+{start_y}")

        # Start animation
        self._animate()

        # Auto-wander
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

                # Make white/near-white pixels transparent
                datas = list(frame.get_flattened_data())
                new_data = []
                for item in datas:
                    # If pixel is very close to white and has high alpha, make it transparent
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

        # Update the displayed frame
        self.current_frame = self.current_frame % len(frames)
        self.canvas.itemconfig(self.photo_item, image=frames[self.current_frame])
        self.current_frame += 1

        # Schedule next frame
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
        self.drag_offset = (event.x, event.y)

    def _on_drag(self, event):
        """Move the pet while dragging."""
        if self.dragging:
            x = self.root.winfo_x() + event.x - self.drag_offset[0]
            y = self.root.winfo_y() + event.y - self.drag_offset[1]
            self.root.geometry(f"+{x}+{y}")

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

            # Choose a random action
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

            # Sometimes go back to idle after a moment
            if action != "idle":
                self.root.after(2000, lambda: self.set_state("idle") if not self.dragging else None)

            self.wander_job = self.root.after(WANDER_INTERVAL, wander)

        self.wander_job = self.root.after(WANDER_INTERVAL, wander)

    def _stop_wander(self):
        """Stop wandering."""
        if self.wander_job:
            self.root.after_cancel(self.wander_job)
            self.wander_job = None
        self.set_state("idle")

    def _move_pet(self, dx: int, dy: int):
        """Move the pet window by dx, dy pixels."""
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy

        # Keep within screen bounds
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max(0, min(x, screen_w - self.frame_w))
        y = max(0, min(y, screen_h - self.frame_h))

        self.root.geometry(f"+{x}+{y}")

    def _quit(self):
        """Exit the pet."""
        self._stop_wander()
        self.root.destroy()

    def run(self):
        """Start the pet application."""
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Desktop Pet Player")
    parser.add_argument("--atlas", required=True, help="Path to sprite atlas PNG")
    parser.add_argument("--manifest", default=None, help="Path to pet.json manifest")
    parser.add_argument("--scale", type=float, default=2.0, help="Display scale factor")
    args = parser.parse_args()

    if not os.path.exists(args.atlas):
        print(f"ERROR: Atlas not found: {args.atlas}")
        sys.exit(1)

    pet = DesktopPet(args.atlas, args.manifest, args.scale)
    pet.run()


if __name__ == "__main__":
    main()
