"""
make_contact_sheet.py - Generate a contact sheet / thumbnail grid of the sprite atlas.

Usage:
    python make_contact_sheet.py --atlas <atlas.png> --output <contact_sheet.png>
"""

import argparse
from PIL import Image, ImageDraw, ImageFont

FRAME_WIDTH = 192
FRAME_HEIGHT = 208
COLUMNS = 8
ROWS = 9

STATE_NAMES = [
    "idle", "running-right", "running-left", "waving",
    "jumping", "failed", "waiting", "running", "review",
]


def make_contact_sheet(atlas_path: str, output_path: str, thumb_scale: float = 0.5):
    """Generate a labeled contact sheet from the sprite atlas."""
    img = Image.open(atlas_path).convert("RGBA")
    tw = int(FRAME_WIDTH * thumb_scale)
    th = int(FRAME_HEIGHT * thumb_scale)
    label_h = 16
    margin = 2

    total_w = COLUMNS * (tw + margin) + margin
    total_h = ROWS * (th + label_h + margin) + margin

    sheet = Image.new("RGBA", (total_w, total_h), (40, 40, 40, 255))
    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for row in range(ROWS):
        for col in range(COLUMNS):
            x1 = col * FRAME_WIDTH
            y1 = row * FRAME_HEIGHT
            x2 = x1 + FRAME_WIDTH
            y2 = y1 + FRAME_HEIGHT

            cell = img.crop((x1, y1, x2, y2))
            cell_thumb = cell.resize((tw, th), Image.LANCZOS)

            tx = margin + col * (tw + margin)
            ty = margin + row * (th + label_h + margin) + label_h

            sheet.paste(cell_thumb, (tx, ty))

            # Label for first column
            if col == 0:
                label = STATE_NAMES[row] if row < len(STATE_NAMES) else f"row-{row}"
                draw.text((tx, ty - label_h), label, fill=(255, 255, 255, 255), font=font)

    sheet.save(output_path, "PNG")
    print(f"Contact sheet saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate contact sheet from atlas")
    parser.add_argument("--atlas", required=True, help="Input atlas PNG path")
    parser.add_argument("--output", required=True, help="Output contact sheet PNG path")
    parser.add_argument("--scale", type=float, default=0.5, help="Thumbnail scale factor")
    args = parser.parse_args()

    make_contact_sheet(args.atlas, args.output, args.scale)


if __name__ == "__main__":
    main()
