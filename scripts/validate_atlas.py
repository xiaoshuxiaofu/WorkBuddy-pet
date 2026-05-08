"""
validate_atlas.py - Validate a sprite atlas against the Codex Pet Contract.

Usage:
    python validate_atlas.py --atlas <atlas.png> [--manifest <pet.json>]
"""

import os
import json
import argparse
from PIL import Image

EXPECTED_WIDTH = 1536
EXPECTED_HEIGHT = 1872
EXPECTED_COLS = 8
EXPECTED_ROWS = 9
FRAME_WIDTH = 192
FRAME_HEIGHT = 208
EXPECTED_STATES = [
    "idle", "running-right", "running-left", "waving",
    "jumping", "failed", "waiting", "running", "review",
]


def validate_atlas(atlas_path: str, manifest_path: str = None):
    """Validate a sprite atlas image and optionally its manifest."""
    errors = []
    warnings = []

    # Validate image
    if not os.path.exists(atlas_path):
        return [f"Atlas file not found: {atlas_path}"], []

    try:
        img = Image.open(atlas_path)
    except Exception as e:
        return [f"Cannot open atlas image: {e}"], []

    w, h = img.size
    if w != EXPECTED_WIDTH:
        errors.append(f"Atlas width is {w}, expected {EXPECTED_WIDTH}")
    if h != EXPECTED_HEIGHT:
        errors.append(f"Atlas height is {h}, expected {EXPECTED_HEIGHT}")

    # Check for non-transparent content in each cell
    empty_cells = []
    for row in range(EXPECTED_ROWS):
        for col in range(EXPECTED_COLS):
            x1 = col * FRAME_WIDTH
            y1 = row * FRAME_HEIGHT
            x2 = x1 + FRAME_WIDTH
            y2 = y1 + FRAME_HEIGHT
            cell = img.crop((x1, y1, x2, y2))
            # Check if cell has any non-transparent pixels
            if cell.mode == "RGBA":
                alpha = cell.split()[3]
                if alpha.getextrema() == (0, 0):
                    empty_cells.append(f"Row {row} ({EXPECTED_STATES[row] if row < len(EXPECTED_STATES) else 'unknown'}), Col {col}")

    if empty_cells:
        warnings.append(f"Found {len(empty_cells)} empty/transparent cells: {', '.join(empty_cells[:5])}{'...' if len(empty_cells) > 5 else ''}")

    # Validate manifest
    if manifest_path and os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        if manifest.get("frame_width") != FRAME_WIDTH:
            errors.append(f"Manifest frame_width is {manifest.get('frame_width')}, expected {FRAME_WIDTH}")
        if manifest.get("frame_height") != FRAME_HEIGHT:
            errors.append(f"Manifest frame_height is {manifest.get('frame_height')}, expected {FRAME_HEIGHT}")
        if manifest.get("columns") != EXPECTED_COLS:
            errors.append(f"Manifest columns is {manifest.get('columns')}, expected {EXPECTED_COLS}")

        manifest_states = [s["name"] for s in manifest.get("states", [])]
        for expected in EXPECTED_STATES:
            if expected not in manifest_states:
                warnings.append(f"Missing state in manifest: {expected}")

    # Print results
    print(f"\n=== Atlas Validation: {atlas_path} ===")
    print(f"Image size: {w}x{h}")
    print(f"Status: {'PASS' if not errors else 'FAIL'}")

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    if not errors and not warnings:
        print("  All checks passed!")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate a sprite atlas")
    parser.add_argument("--atlas", required=True, help="Path to atlas PNG")
    parser.add_argument("--manifest", default=None, help="Path to pet.json manifest")
    args = parser.parse_args()

    validate_atlas(args.atlas, args.manifest)


if __name__ == "__main__":
    main()
