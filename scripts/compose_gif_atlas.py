"""
compose_gif_atlas.py - Compose a Codex sprite atlas from individual animated GIFs,
one per state. Each GIF's frames are extracted and placed into the atlas grid.

Usage:
    python compose_gif_atlas.py --gifs-dir <dir> --output <output_dir> --name <pet_name>
"""
import os
import sys
import json
import argparse
from PIL import Image, ImageSequence

FRAME_WIDTH = 192
FRAME_HEIGHT = 208
COLUMNS = 8
ROWS = 9

STATE_ORDER = [
    "idle", "running-right", "running-left", "waving",
    "jumping", "failed", "waiting", "running", "review",
]

# Default Codex timing for states (used when GIF has no duration info)
DEFAULT_DURATIONS = {
    "idle":          [280, 110, 110, 140, 140, 320],
    "running-right": [120, 120, 120, 120, 120, 120, 120, 220],
    "running-left":  [120, 120, 120, 120, 120, 120, 120, 220],
    "waving":        [140, 140, 140, 280],
    "jumping":       [140, 140, 140, 140, 280],
    "failed":        [140, 140, 140, 140, 140, 140, 140, 240],
    "waiting":       [150, 150, 150, 150, 150, 260],
    "running":       [120, 120, 120, 120, 120, 220],
    "review":        [150, 150, 150, 150, 150, 280],
}


def find_gif(gifs_dir: str, state: str) -> str | None:
    """Find a GIF file matching a state name using common naming patterns."""
    entries = os.listdir(gifs_dir)
    # Try exact state match first, then fuzzy
    patterns = [
        lambda e: e.lower() == f"{state}.gif",
        lambda e: e.lower().endswith(f"-{state}.gif"),
        lambda e: state in e.lower() and e.lower().endswith(".gif"),
    ]
    for pat in patterns:
        for entry in entries:
            if pat(entry):
                return os.path.join(gifs_dir, entry)
    return None


def extract_frames(gif_path: str) -> list[Image.Image]:
    """Extract all frames from a GIF as RGBA images."""
    gif = Image.open(gif_path)
    frames = []
    for frame in ImageSequence.Iterator(gif):
        # Convert palette mode to RGBA, preserving transparency
        rgba = frame.convert("RGBA")
        frames.append(rgba.copy())
    return frames


def compose_atlas(gifs_dir: str, output_dir: str, pet_name: str):
    """Extract GIFs and compose into a Codex atlas."""
    os.makedirs(output_dir, exist_ok=True)

    atlas = Image.new("RGBA", (FRAME_WIDTH * COLUMNS, FRAME_HEIGHT * ROWS), (0, 0, 0, 0))
    states_config = []

    for row, state_name in enumerate(STATE_ORDER):
        gif_path = find_gif(gifs_dir, state_name)
        if gif_path is None:
            print(f"[WARN] No GIF found for state '{state_name}', skipping row {row}")
            states_config.append({
                "name": state_name, "row": row, "frames": 0, "durations": [],
            })
            continue

        print(f"[state] {state_name} <- {os.path.basename(gif_path)}")
        frames = extract_frames(gif_path)
        num_frames = len(frames)

        if num_frames > COLUMNS:
            print(f"[WARN] {state_name} has {num_frames} frames, truncating to {COLUMNS}")
            num_frames = COLUMNS

        # Get durations from GIF or use defaults
        gif = Image.open(gif_path)
        durations = []
        for i, frame in enumerate(ImageSequence.Iterator(gif)):
            if i >= num_frames:
                break
            duration = frame.info.get("duration", 0)
            durations.append(duration if duration > 0 else 100)

        # Verify duration count matches frame count - use defaults if not
        if len(durations) != num_frames:
            durations = DEFAULT_DURATIONS.get(state_name, [100] * num_frames)[:num_frames]

        # Place frames into atlas
        for col in range(num_frames):
            x = col * FRAME_WIDTH
            y = row * FRAME_HEIGHT
            # Resize if needed (shouldn't be, but safety)
            frame = frames[col]
            if frame.size != (FRAME_WIDTH, FRAME_HEIGHT):
                frame = frame.resize((FRAME_WIDTH, FRAME_HEIGHT), Image.LANCZOS)
            atlas.paste(frame, (x, y), frame)

        states_config.append({
            "name": state_name,
            "row": row,
            "frames": num_frames,
            "durations": durations,
        })

        # Clean up
        gif.close()
        for f in frames:
            f.close()

    # Save atlas
    atlas_path = os.path.join(output_dir, f"{pet_name}_atlas.png")
    atlas.save(atlas_path, "PNG")
    size_kb = os.path.getsize(atlas_path) / 1024
    print(f"\nAtlas saved: {atlas_path} ({size_kb:.1f} KB)")

    # Save manifest
    manifest = {
        "name": pet_name,
        "version": "1.0",
        "frame_width": FRAME_WIDTH,
        "frame_height": FRAME_HEIGHT,
        "columns": COLUMNS,
        "states": states_config,
    }
    manifest_path = os.path.join(output_dir, "pet.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifest saved: {manifest_path}")

    return atlas_path, manifest_path


def main():
    parser = argparse.ArgumentParser(description="Compose Codex atlas from GIF files")
    parser.add_argument("--gifs-dir", required=True, help="Directory containing per-state GIFs")
    parser.add_argument("--output", required=True, help="Output directory for atlas and manifest")
    parser.add_argument("--name", required=True, help="Pet name")
    args = parser.parse_args()

    if not os.path.isdir(args.gifs_dir):
        print(f"ERROR: GIFs directory not found: {args.gifs_dir}", file=sys.stderr)
        sys.exit(1)

    compose_atlas(args.gifs_dir, args.output, args.name)


if __name__ == "__main__":
    main()
