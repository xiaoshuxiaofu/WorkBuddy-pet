"""
generate_demo_atlas.py - Generate a demo sprite atlas with a cute pixel-art character.

Creates a simple animated character (a round blue slime creature)
with 9 animation states, each with 8 frames.

Usage:
    python generate_demo_atlas.py --output <output_dir>
"""

import os
import json
import math
import argparse
from PIL import Image, ImageDraw

FRAME_WIDTH = 192
FRAME_HEIGHT = 208
COLUMNS = 8
ROWS = 9

STATE_NAMES = [
    "idle", "running-right", "running-left", "waving",
    "jumping", "failed", "waiting", "running", "review",
]


def draw_slime(draw, cx, cy, size, color, eye_offset_x=0, eye_offset_y=0,
               mouth_type="smile", arm_left=0, arm_right=0, squash=1.0, stretch=1.0):
    """Draw a cute slime character on the given ImageDraw object.

    Args:
        draw: PIL ImageDraw object
        cx, cy: Center position
        size: Base size (radius)
        color: Body color (r, g, b)
        eye_offset_x, eye_offset_y: Eye displacement
        mouth_type: "smile", "sad", "open", "neutral"
        arm_left, arm_right: Arm angle offset (-30 to 30)
        squash: Horizontal scale (1.0 = normal)
        stretch: Vertical scale (1.0 = normal)
    """
    r, g, b = color

    # Shadow
    shadow_w = int(size * 0.8 * squash)
    shadow_h = int(size * 0.15)
    draw.ellipse(
        [cx - shadow_w, cy + size * 0.7, cx + shadow_w, cy + size * 0.7 + shadow_h],
        fill=(0, 0, 0, 40)
    )

    # Body - ellipse with squash/stretch
    body_w = int(size * squash)
    body_h = int(size * stretch)
    # Main body
    draw.ellipse(
        [cx - body_w, cy - body_h, cx + body_w, cy + body_h],
        fill=(r, g, b, 230)
    )
    # Highlight
    hl_r = int(size * 0.6 * squash)
    hl_h = int(size * 0.6 * stretch)
    highlight_color = (min(r + 40, 255), min(g + 40, 255), min(b + 40, 255), 100)
    draw.ellipse(
        [cx - hl_r, cy - hl_h, cx + hl_r, cy + hl_h],
        fill=highlight_color
    )
    # Shine
    shine_x = cx - int(size * 0.3 * squash)
    shine_y = cy - int(size * 0.3 * stretch)
    shine_r = int(size * 0.2)
    draw.ellipse(
        [shine_x - shine_r, shine_y - shine_r, shine_x + shine_r, shine_y + shine_r],
        fill=(255, 255, 255, 120)
    )

    # Eyes
    eye_spacing = int(size * 0.3)
    eye_size = int(size * 0.12)
    eye_y = cy - int(size * 0.15 * stretch) + eye_offset_y

    # Left eye
    lx = cx - eye_spacing + eye_offset_x
    draw.ellipse(
        [lx - eye_size - 2, eye_y - eye_size - 2, lx + eye_size + 2, eye_y + eye_size + 2],
        fill=(255, 255, 255, 240)
    )
    draw.ellipse(
        [lx - eye_size, eye_y - eye_size, lx + eye_size, eye_y + eye_size],
        fill=(40, 40, 60, 250)
    )
    # Pupil highlight
    draw.ellipse(
        [lx - 1, eye_y - eye_size + 1, lx + 3, eye_y - eye_size + 5],
        fill=(255, 255, 255, 200)
    )

    # Right eye
    rx = cx + eye_spacing + eye_offset_x
    draw.ellipse(
        [rx - eye_size - 2, eye_y - eye_size - 2, rx + eye_size + 2, eye_y + eye_size + 2],
        fill=(255, 255, 255, 240)
    )
    draw.ellipse(
        [rx - eye_size, eye_y - eye_size, rx + eye_size, eye_y + eye_size],
        fill=(40, 40, 60, 250)
    )
    draw.ellipse(
        [rx - 1, eye_y - eye_size + 1, rx + 3, eye_y - eye_size + 5],
        fill=(255, 255, 255, 200)
    )

    # Mouth
    mouth_y = cy + int(size * 0.2 * stretch) + eye_offset_y
    mouth_x = cx + eye_offset_x
    if mouth_type == "smile":
        draw.arc(
            [mouth_x - 8, mouth_y - 4, mouth_x + 8, mouth_y + 8],
            start=0, end=180, fill=(40, 40, 60, 220), width=2
        )
    elif mouth_type == "sad":
        draw.arc(
            [mouth_x - 8, mouth_y, mouth_x + 8, mouth_y + 12],
            start=180, end=360, fill=(40, 40, 60, 220), width=2
        )
    elif mouth_type == "open":
        draw.ellipse(
            [mouth_x - 5, mouth_y - 2, mouth_x + 5, mouth_y + 6],
            fill=(40, 40, 60, 200)
        )
    elif mouth_type == "neutral":
        draw.line(
            [mouth_x - 6, mouth_y + 2, mouth_x + 6, mouth_y + 2],
            fill=(40, 40, 60, 220), width=2
        )

    # Arms (simple stubs)
    arm_y = cy + int(size * 0.05 * stretch)
    arm_len = int(size * 0.4)

    # Left arm
    la_angle = -60 + arm_left
    la_rad = math.radians(la_angle)
    la_x = cx - body_w + int(math.cos(la_rad) * 5)
    la_end_x = la_x + int(math.cos(la_rad) * arm_len)
    la_end_y = arm_y + int(math.sin(la_rad) * arm_len)
    draw.line(
        [la_x, arm_y, la_end_x, la_end_y],
        fill=(r, g, b, 200), width=4
    )
    # Hand
    draw.ellipse(
        [la_end_x - 5, la_end_y - 5, la_end_x + 5, la_end_y + 5],
        fill=(min(r + 20, 255), min(g + 20, 255), min(b + 20, 255), 220)
    )

    # Right arm
    ra_angle = -120 + arm_right
    ra_rad = math.radians(ra_angle)
    ra_x = cx + body_w - int(math.cos(math.pi - ra_rad) * 5)
    ra_end_x = ra_x + int(math.cos(ra_rad) * arm_len)
    ra_end_y = arm_y + int(math.sin(ra_rad) * arm_len)
    draw.line(
        [ra_x, arm_y, ra_end_x, ra_end_y],
        fill=(r, g, b, 200), width=4
    )
    draw.ellipse(
        [ra_end_x - 5, ra_end_y - 5, ra_end_x + 5, ra_end_y + 5],
        fill=(min(r + 20, 255), min(g + 20, 255), min(b + 20, 255), 220)
    )


def generate_demo_atlas(output_dir: str, pet_name: str = "blue-slime"):
    """Generate a complete demo sprite atlas."""
    os.makedirs(output_dir, exist_ok=True)

    atlas = Image.new("RGBA", (FRAME_WIDTH * COLUMNS, FRAME_HEIGHT * ROWS), (0, 0, 0, 0))
    color = (80, 160, 255)  # Blue slime
    base_size = 50  # Base radius
    cx = FRAME_WIDTH // 2
    cy = FRAME_HEIGHT // 2 + 20

    states_config = []

    for row, state_name in enumerate(STATE_NAMES):
        for col in range(COLUMNS):
            frame = Image.new("RGBA", (FRAME_WIDTH, FRAME_HEIGHT), (0, 0, 0, 0))
            draw = ImageDraw.Draw(frame)
            t = col / max(COLUMNS - 1, 1)  # 0.0 to 1.0

            if state_name == "idle":
                # Gentle breathing / bobbing
                offset_y = math.sin(t * 2 * math.pi) * 5
                squash = 1.0 + math.sin(t * 2 * math.pi) * 0.03
                stretch = 1.0 - math.sin(t * 2 * math.pi) * 0.03
                draw_slime(draw, cx, cy + offset_y, base_size, color,
                           squash=squash, stretch=stretch)

            elif state_name == "running-right":
                # Running to the right with leg-like bounce
                offset_x = math.sin(t * 2 * math.pi) * 3
                offset_y = -abs(math.sin(t * 2 * math.pi)) * 8
                squash = 1.0 - abs(math.sin(t * 2 * math.pi)) * 0.05
                stretch = 1.0 + abs(math.sin(t * 2 * math.pi)) * 0.05
                draw_slime(draw, cx + offset_x, cy + offset_y, base_size, color,
                           eye_offset_x=3, squash=squash, stretch=stretch,
                           arm_left=-10 + math.sin(t * 2 * math.pi) * 20,
                           arm_right=-10 - math.sin(t * 2 * math.pi) * 20)

            elif state_name == "running-left":
                # Running to the left (mirror)
                offset_x = -math.sin(t * 2 * math.pi) * 3
                offset_y = -abs(math.sin(t * 2 * math.pi)) * 8
                squash = 1.0 - abs(math.sin(t * 2 * math.pi)) * 0.05
                stretch = 1.0 + abs(math.sin(t * 2 * math.pi)) * 0.05
                draw_slime(draw, cx + offset_x, cy + offset_y, base_size, color,
                           eye_offset_x=-3, squash=squash, stretch=stretch,
                           arm_left=-10 - math.sin(t * 2 * math.pi) * 20,
                           arm_right=-10 + math.sin(t * 2 * math.pi) * 20)

            elif state_name == "waving":
                # Waving right arm
                wave_angle = math.sin(t * 2 * math.pi) * 40
                offset_y = math.sin(t * 2 * math.pi) * 2
                draw_slime(draw, cx, cy + offset_y, base_size, color,
                           mouth_type="smile",
                           arm_right=-80 + wave_angle)

            elif state_name == "jumping":
                # Jumping up and down
                offset_y = -abs(math.sin(t * math.pi)) * 30
                squash = 1.0 + (1 - abs(math.sin(t * math.pi))) * 0.1
                stretch = 1.0 + abs(math.sin(t * math.pi)) * 0.1
                if abs(math.sin(t * math.pi)) < 0.1:
                    # Landing squash
                    squash = 1.15
                    stretch = 0.85
                draw_slime(draw, cx, cy + offset_y, base_size, color,
                           mouth_type="open", squash=squash, stretch=stretch,
                           arm_left=-30, arm_right=-30)

            elif state_name == "failed":
                # Sad/failed
                wobble = math.sin(t * 3 * math.pi) * 3
                squash = 1.05
                stretch = 0.95
                draw_slime(draw, cx + wobble, cy + 5, base_size, color,
                           eye_offset_y=3, mouth_type="sad",
                           squash=squash, stretch=stretch,
                           arm_left=20, arm_right=20)

            elif state_name == "waiting":
                # Looking around, waiting
                look_x = math.sin(t * 2 * math.pi) * 5
                offset_y = math.sin(t * 4 * math.pi) * 2
                draw_slime(draw, cx, cy + offset_y, base_size, color,
                           eye_offset_x=int(look_x), mouth_type="neutral")

            elif state_name == "running":
                # Running in place
                offset_y = -abs(math.sin(t * 2 * math.pi)) * 10
                squash = 1.0 - abs(math.sin(t * 2 * math.pi)) * 0.08
                stretch = 1.0 + abs(math.sin(t * 2 * math.pi)) * 0.08
                draw_slime(draw, cx, cy + offset_y, base_size, color,
                           mouth_type="open", squash=squash, stretch=stretch,
                           arm_left=-10 + math.sin(t * 2 * math.pi) * 25,
                           arm_right=-10 - math.sin(t * 2 * math.pi) * 25)

            elif state_name == "review":
                # Looking at code, inspecting
                look_x = math.sin(t * 2 * math.pi) * 3
                tilt = math.sin(t * 2 * math.pi) * 0.03
                draw_slime(draw, cx, cy, base_size, color,
                           eye_offset_x=int(look_x), eye_offset_y=-2,
                           mouth_type="neutral",
                           arm_right=-60 + math.sin(t * math.pi) * 10)

            # Paste frame into atlas
            x = col * FRAME_WIDTH
            y = row * FRAME_HEIGHT
            atlas.paste(frame, (x, y), frame)

        fps = 10
        if state_name in ("idle", "waiting", "review"):
            fps = 8
        elif state_name == "failed":
            fps = 6

        states_config.append({
            "name": state_name,
            "row": row,
            "frames": COLUMNS,
            "fps": fps,
        })

    # Save atlas
    atlas_path = os.path.join(output_dir, f"{pet_name}_atlas.png")
    atlas.save(atlas_path, "PNG")
    print(f"Atlas saved to {atlas_path}")

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
    print(f"Manifest saved to {manifest_path}")

    return atlas_path, manifest_path


def main():
    parser = argparse.ArgumentParser(description="Generate demo sprite atlas")
    parser.add_argument("--output", default="./output/pets/demo", help="Output directory")
    parser.add_argument("--name", default="blue-slime", help="Pet name")
    args = parser.parse_args()

    generate_demo_atlas(args.output, args.name)


if __name__ == "__main__":
    main()
