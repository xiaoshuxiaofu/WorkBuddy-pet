"""
extract_strip_frames.py - Extract individual frames from a strip/image.

Given an image that contains one row of animation frames,
extract each frame into individual PNG files.

Usage:
    python extract_strip_frames.py --input <strip.png> --output-dir <frames_dir> --state <state_name> [--num-frames 8]
"""

import os
import argparse
from PIL import Image

FRAME_WIDTH = 192
FRAME_HEIGHT = 208


def extract_frames(input_path: str, output_dir: str, state_name: str, num_frames: int = 8):
    """Extract frames from a strip image into individual PNG files."""
    os.makedirs(os.path.join(output_dir, state_name), exist_ok=True)

    img = Image.open(input_path).convert("RGBA")
    img_w, img_h = img.size

    # Try to auto-detect frame count if not specified
    detected_cols = img_w // FRAME_WIDTH
    if detected_cols < 1:
        detected_cols = 1

    cols = min(detected_cols, num_frames) if num_frames else detected_cols

    extracted = 0
    for i in range(cols):
        x1 = i * FRAME_WIDTH
        y1 = 0
        x2 = x1 + FRAME_WIDTH
        y2 = FRAME_HEIGHT

        if x2 > img_w or y2 > img_h:
            break

        frame = img.crop((x1, y1, x2, y2))
        frame_path = os.path.join(output_dir, state_name, f"frame_{i}.png")
        frame.save(frame_path, "PNG")
        extracted += 1

    print(f"Extracted {extracted} frames for state '{state_name}' to {output_dir}/{state_name}/")
    return extracted


def main():
    parser = argparse.ArgumentParser(description="Extract frames from strip image")
    parser.add_argument("--input", required=True, help="Input strip image path")
    parser.add_argument("--output-dir", required=True, help="Output directory for frames")
    parser.add_argument("--state", required=True, help="Animation state name")
    parser.add_argument("--num-frames", type=int, default=8, help="Number of frames to extract")
    args = parser.parse_args()

    extract_frames(args.input, args.output_dir, args.state, args.num_frames)


if __name__ == "__main__":
    main()
