"""
compose_atlas.py - Compose sprite atlas from individual frame images.

Usage:
    python compose_atlas.py --input-dir <frames_dir> --output <atlas.png>

Expected input structure:
    frames_dir/
        idle/       frame_0.png ... frame_7.png
        running-right/  frame_0.png ... frame_7.png
        ... (9 states total)
"""

import os
import json
import argparse
from PIL import Image

STATES_ORDER = [
    "idle",
    "running-right",
    "running-left",
    "waving",
    "jumping",
    "failed",
    "waiting",
    "running",
    "review",
]

FRAME_WIDTH = 192
FRAME_HEIGHT = 208
COLUMNS = 8
ROWS = 9


def compose_atlas(input_dir: str, output_path: str, pet_name: str = "pet"):
    """Compose a sprite atlas from individual frame directories."""
    atlas = Image.new("RGBA", (FRAME_WIDTH * COLUMNS, FRAME_HEIGHT * ROWS), (0, 0, 0, 0))
    manifest_states = []

    for row_idx, state_name in enumerate(STATES_ORDER):
        state_dir = os.path.join(input_dir, state_name)
        if not os.path.isdir(state_dir):
            print(f"WARNING: Missing state directory: {state_dir}, filling with blank row")
            continue

        frames = sorted([f for f in os.listdir(state_dir) if f.endswith(".png")])
        if not frames:
            print(f"WARNING: No frames found in {state_dir}")
            continue

        fps = 10
        if state_name in ("idle", "waiting", "review"):
            fps = 8
        elif state_name == "failed":
            fps = 6

        manifest_states.append({
            "name": state_name,
            "row": row_idx,
            "frames": min(len(frames), COLUMNS),
            "fps": fps,
        })

        for col_idx, frame_file in enumerate(frames[:COLUMNS]):
            frame_path = os.path.join(state_dir, frame_file)
            try:
                frame_img = Image.open(frame_path).convert("RGBA")
                frame_img = frame_img.resize((FRAME_WIDTH, FRAME_HEIGHT), Image.LANCZOS)
                x = col_idx * FRAME_WIDTH
                y = row_idx * FRAME_HEIGHT
                atlas.paste(frame_img, (x, y), frame_img)
            except Exception as e:
                print(f"ERROR: Failed to process {frame_path}: {e}")

    atlas.save(output_path, "PNG")
    print(f"Atlas saved to {output_path} ({atlas.size[0]}x{atlas.size[1]})")

    # Save manifest
    manifest = {
        "name": pet_name,
        "version": "1.0",
        "frame_width": FRAME_WIDTH,
        "frame_height": FRAME_HEIGHT,
        "columns": COLUMNS,
        "states": manifest_states,
    }
    manifest_path = os.path.splitext(output_path)[0] + "_manifest.json"
    # Actually save as pet.json in the same directory
    pet_dir = os.path.dirname(output_path)
    pet_json_path = os.path.join(pet_dir, "pet.json")
    with open(pet_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifest saved to {pet_json_path}")

    return atlas, manifest


def main():
    parser = argparse.ArgumentParser(description="Compose sprite atlas from frame images")
    parser.add_argument("--input-dir", required=True, help="Directory containing state subdirectories with frames")
    parser.add_argument("--output", required=True, help="Output atlas PNG path")
    parser.add_argument("--name", default="pet", help="Pet name for manifest")
    args = parser.parse_args()

    compose_atlas(args.input_dir, args.output, args.name)


if __name__ == "__main__":
    main()
