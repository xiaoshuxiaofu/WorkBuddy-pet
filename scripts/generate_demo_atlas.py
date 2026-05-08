"""
generate_demo_atlas.py - Generate sprite atlases for WorkBuddy desktop pets.

Creates pixel-art characters with 9 animation states, each with 8 frames.
Supports multiple creature types via presets or custom color parameters.

Usage:
    python generate_demo_atlas.py --output <output_dir>                    # blue slime (default)
    python generate_demo_atlas.py --output <dir> --preset kunkun           # dark teal slime
    python generate_demo_atlas.py --output <dir> --preset milk-frog        # orange frog
    python generate_demo_atlas.py --output <dir> --name mypet --body 255,128,64 --type frog
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

# Codex-style per-frame durations (ms) and frame counts per state
STATE_CONFIG = {
    "idle":          {"frames": 6, "durations": [280, 110, 110, 140, 140, 320]},
    "running-right": {"frames": 8, "durations": [120, 120, 120, 120, 120, 120, 120, 220]},
    "running-left":  {"frames": 8, "durations": [120, 120, 120, 120, 120, 120, 120, 220]},
    "waving":        {"frames": 4, "durations": [140, 140, 140, 280]},
    "jumping":       {"frames": 5, "durations": [140, 140, 140, 140, 280]},
    "failed":        {"frames": 8, "durations": [140, 140, 140, 140, 140, 140, 140, 240]},
    "waiting":       {"frames": 6, "durations": [150, 150, 150, 150, 150, 260]},
    "running":       {"frames": 6, "durations": [120, 120, 120, 120, 120, 220]},
    "review":        {"frames": 6, "durations": [150, 150, 150, 150, 150, 280]},
}

# Preset creature definitions: (body_color, eye_color, accent_color, creature_type)
PRESETS = {
    "blue-slime":  {"body": (80, 160, 255), "eye": (40, 40, 60),   "accent": (130, 200, 255), "type": "slime"},
    "kunkun":      {"body": (30, 30, 40),    "eye": (200, 230, 240), "accent": (100, 180, 200), "type": "slime"},
    "milk-frog":   {"body": (230, 160, 50),  "eye": (40, 60, 40),   "accent": (255, 200, 80),  "type": "frog"},
}


def draw_creature(draw, cx, cy, size, body_color, eye_color=(40, 40, 60),
                  accent_color=None, eye_offset_x=0, eye_offset_y=0,
                  mouth_type="smile", arm_left=0, arm_right=0,
                  squash=1.0, stretch=1.0, creature_type="slime"):
    """Draw a pixel-art creature on the given ImageDraw.

    Args:
        creature_type: "slime" (round blob) or "frog" (wider body with eye bumps).
        All other args control positioning and animation offsets.
    """
    r, g, b = body_color
    if accent_color is None:
        accent_color = (min(r + 40, 255), min(g + 40, 255), min(b + 40, 255))

    body_w = int(size * squash)
    body_h = int(size * stretch)

    # ── Shadow ──
    shadow_w = int(size * 0.8 * squash)
    shadow_h = int(size * 0.15)
    draw.ellipse(
        [cx - shadow_w, cy + size * 0.7, cx + shadow_w, cy + size * 0.7 + shadow_h],
        fill=(0, 0, 0, 40),
    )

    # ── Body ──
    if creature_type == "frog":
        # Wider, flatter body
        draw.ellipse(
            [cx - int(body_w * 1.3), cy - int(body_h * 0.7),
             cx + int(body_w * 1.3), cy + int(body_h * 0.7)],
            fill=(r, g, b, 230),
        )
        # Lighter belly
        belly = (min(r + 60, 255), min(g + 60, 255), min(b + 60, 255), 200)
        draw.ellipse(
            [cx - int(body_w * 0.8), cy - int(body_h * 0.2),
             cx + int(body_w * 0.8), cy + int(body_h * 0.5)],
            fill=belly,
        )
        # Eye bumps on top
        bump_r = int(size * 0.25)
        for side in (-1, 1):
            bcx = cx + side * int(size * 0.4)
            draw.ellipse(
                [bcx - bump_r, cy - int(size * 0.6) - bump_r,
                 bcx + bump_r, cy - int(size * 0.6) + bump_r],
                fill=(r, g, b, 230),
            )
    else:
        # Standard slime body
        draw.ellipse(
            [cx - body_w, cy - body_h, cx + body_w, cy + body_h],
            fill=(r, g, b, 230),
        )
        # Highlight patch
        hl_r = int(size * 0.6 * squash)
        hl_h = int(size * 0.6 * stretch)
        draw.ellipse(
            [cx - hl_r, cy - hl_h, cx + hl_r, cy + hl_h],
            fill=(*accent_color, 100),
        )

    # ── Shine spot ──
    shine_x = cx - int(size * 0.3 * squash)
    shine_y = cy - int(size * 0.3 * stretch)
    shine_r = int(size * 0.2)
    draw.ellipse(
        [shine_x - shine_r, shine_y - shine_r, shine_x + shine_r, shine_y + shine_r],
        fill=(255, 255, 255, 120),
    )

    # ── Eyes ──
    eye_spacing = int(size * 0.3)
    eye_size = int(size * 0.12)
    eye_y = cy - int(size * 0.15 * stretch) + eye_offset_y
    if creature_type == "frog":
        eye_y = cy - int(size * 0.4)
        eye_size = int(size * 0.15)

    for base_x in (cx - eye_spacing, cx + eye_spacing):
        ex = base_x + eye_offset_x
        draw.ellipse(
            [ex - eye_size - 2, eye_y - eye_size - 2,
             ex + eye_size + 2, eye_y + eye_size + 2],
            fill=(255, 255, 255, 240),
        )
        draw.ellipse(
            [ex - eye_size, eye_y - eye_size, ex + eye_size, eye_y + eye_size],
            fill=(*eye_color, 250),
        )
        draw.ellipse(
            [ex - 1, eye_y - eye_size + 1, ex + 3, eye_y - eye_size + 5],
            fill=(255, 255, 255, 200),
        )

    # ── Mouth ──
    mouth_y = cy + int(size * 0.2 * stretch) + eye_offset_y
    mouth_x = cx + eye_offset_x
    if creature_type == "frog":
        mouth_y = cy + int(size * 0.05)

    mouth_color = (*eye_color, 220)
    if mouth_type == "smile":
        draw.arc([mouth_x - 10, mouth_y - 6, mouth_x + 10, mouth_y + 10],
                 start=0, end=180, fill=mouth_color, width=2)
    elif mouth_type == "sad":
        draw.arc([mouth_x - 10, mouth_y, mouth_x + 10, mouth_y + 14],
                 start=180, end=360, fill=mouth_color, width=2)
    elif mouth_type == "open":
        draw.ellipse([mouth_x - 6, mouth_y - 2, mouth_x + 6, mouth_y + 8],
                     fill=(*eye_color, 200))
    elif mouth_type == "neutral":
        draw.line([mouth_x - 8, mouth_y + 3, mouth_x + 8, mouth_y + 3],
                  fill=mouth_color, width=2)

    # ── Arms ──
    arm_y = cy + int(size * 0.05 * stretch)
    arm_len = int(size * 0.4)
    line_w = 4
    hand_r = 5
    if creature_type == "frog":
        arm_y = cy - int(size * 0.1)
        arm_len = int(size * 0.5)
        line_w = 5
        hand_r = 6

    for side, base_x, base_angle in [("left", cx - body_w, -60), ("right", cx + body_w, -120)]:
        angle = base_angle + (arm_left if side == "left" else arm_right)
        rad = math.radians(angle)
        if side == "left":
            ax = base_x + int(math.cos(rad) * 5)
        else:
            ax = base_x - int(math.cos(math.pi - rad) * 5)
        end_x = ax + int(math.cos(rad) * arm_len)
        end_y = arm_y + int(math.sin(rad) * arm_len)
        draw.line([ax, arm_y, end_x, end_y], fill=(r, g, b, 200), width=line_w)
        draw.ellipse(
            [end_x - hand_r, end_y - hand_r, end_x + hand_r, end_y + hand_r],
            fill=(*accent_color, 220),
        )


def generate_atlas(output_dir: str, pet_name: str,
                   body_color: tuple, eye_color: tuple = (40, 40, 60),
                   accent_color: tuple = None, creature_type: str = "slime"):
    """Generate a complete sprite atlas and manifest."""
    os.makedirs(output_dir, exist_ok=True)

    atlas = Image.new("RGBA", (FRAME_WIDTH * COLUMNS, FRAME_HEIGHT * ROWS), (0, 0, 0, 0))
    if accent_color is None:
        accent_color = (min(body_color[0] + 40, 255), min(body_color[1] + 40, 255),
                        min(body_color[2] + 40, 255))

    base_size = 50
    cx = FRAME_WIDTH // 2
    cy = FRAME_HEIGHT // 2 + 20
    states_config = []

    for row, state_name in enumerate(STATE_NAMES):
        num_frames = STATE_CONFIG[state_name]["frames"]
        for col in range(num_frames):
            frame = Image.new("RGBA", (FRAME_WIDTH, FRAME_HEIGHT), (0, 0, 0, 0))
            d = ImageDraw.Draw(frame)
            t = col / max(num_frames - 1, 1)

            kwargs = {
                "body_color": body_color,
                "eye_color": eye_color,
                "accent_color": accent_color,
                "creature_type": creature_type,
            }

            if state_name == "idle":
                offset_y = math.sin(t * 2 * math.pi) * 5
                draw_creature(d, cx, cy + offset_y, base_size,
                              squash=1.0 + math.sin(t * 2 * math.pi) * 0.03,
                              stretch=1.0 - math.sin(t * 2 * math.pi) * 0.03,
                              **kwargs)

            elif state_name == "running-right":
                boff = abs(math.sin(t * 2 * math.pi))
                draw_creature(d, cx + math.sin(t * 2 * math.pi) * 3, cy - boff * 8, base_size,
                              eye_offset_x=3,
                              squash=1.0 - boff * 0.05, stretch=1.0 + boff * 0.05,
                              arm_left=-10 + math.sin(t * 2 * math.pi) * 20,
                              arm_right=-10 - math.sin(t * 2 * math.pi) * 20,
                              **kwargs)

            elif state_name == "running-left":
                boff = abs(math.sin(t * 2 * math.pi))
                draw_creature(d, cx - math.sin(t * 2 * math.pi) * 3, cy - boff * 8, base_size,
                              eye_offset_x=-3,
                              squash=1.0 - boff * 0.05, stretch=1.0 + boff * 0.05,
                              arm_left=-10 - math.sin(t * 2 * math.pi) * 20,
                              arm_right=-10 + math.sin(t * 2 * math.pi) * 20,
                              **kwargs)

            elif state_name == "waving":
                wave = math.sin(t * 2 * math.pi)
                draw_creature(d, cx, cy + wave * 2, base_size,
                              mouth_type="smile", arm_right=-80 + wave * 40, **kwargs)

            elif state_name == "jumping":
                jmp = abs(math.sin(t * math.pi))
                sq, st = 1.0 + (1 - jmp) * 0.1, 1.0 + jmp * 0.1
                if jmp < 0.1:
                    sq, st = 1.15, 0.85
                draw_creature(d, cx, cy - jmp * 30, base_size,
                              mouth_type="open", squash=sq, stretch=st,
                              arm_left=-30, arm_right=-30, **kwargs)

            elif state_name == "failed":
                draw_creature(d, cx + math.sin(t * 3 * math.pi) * 3, cy + 5, base_size,
                              eye_offset_y=3, mouth_type="sad",
                              squash=1.05, stretch=0.95,
                              arm_left=20, arm_right=20, **kwargs)

            elif state_name == "waiting":
                draw_creature(d, cx, cy + math.sin(t * 4 * math.pi) * 2, base_size,
                              eye_offset_x=int(math.sin(t * 2 * math.pi) * 5),
                              mouth_type="neutral", **kwargs)

            elif state_name == "running":
                boff = abs(math.sin(t * 2 * math.pi))
                draw_creature(d, cx, cy - boff * 10, base_size,
                              mouth_type="open",
                              squash=1.0 - boff * 0.08, stretch=1.0 + boff * 0.08,
                              arm_left=-10 + math.sin(t * 2 * math.pi) * 25,
                              arm_right=-10 - math.sin(t * 2 * math.pi) * 25,
                              **kwargs)

            elif state_name == "review":
                draw_creature(d, cx, cy, base_size,
                              eye_offset_x=int(math.sin(t * 2 * math.pi) * 3),
                              eye_offset_y=-2, mouth_type="neutral",
                              arm_right=-60 + math.sin(t * math.pi) * 10,
                              **kwargs)

            x = col * FRAME_WIDTH
            y = row * FRAME_HEIGHT
            atlas.paste(frame, (x, y), frame)

        cfg = STATE_CONFIG[state_name]
        states_config.append({
            "name": state_name,
            "row": row,
            "frames": cfg["frames"],
            "durations": cfg["durations"],
        })

    # Save atlas
    atlas_path = os.path.join(output_dir, f"{pet_name}_atlas.png")
    atlas.save(atlas_path, "PNG")
    print(f"Atlas saved to {atlas_path}")

    # Save manifest
    manifest = {
        "name": pet_name, "version": "1.0",
        "frame_width": FRAME_WIDTH, "frame_height": FRAME_HEIGHT,
        "columns": COLUMNS, "states": states_config,
    }
    manifest_path = os.path.join(output_dir, "pet.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifest saved to {manifest_path}")

    return atlas_path, manifest_path


def main():
    parser = argparse.ArgumentParser(description="Generate a WorkBuddy pet sprite atlas.")
    parser.add_argument("--output", required=True, help="Output directory for atlas and manifest.")
    parser.add_argument("--name", default="blue-slime", help="Base name for the pet (default: blue-slime).")
    parser.add_argument("--preset", choices=list(PRESETS.keys()),
                        help="Use a built-in preset (overrides --type and color args).")
    parser.add_argument("--type", choices=["slime", "frog"], default="slime",
                        help="Creature body type (default: slime).")
    parser.add_argument("--body", help="Body color as R,G,B (e.g. 80,160,255).")
    parser.add_argument("--eye", help="Eye color as R,G,B (e.g. 40,40,60).")
    parser.add_argument("--accent", help="Accent/hand color as R,G,B.")
    args = parser.parse_args()

    # Resolve preset or build from arguments
    if args.preset:
        p = PRESETS[args.preset]
        body_color = p["body"]
        eye_color = p["eye"]
        accent_color = p["accent"]
        creature_type = p["type"]
    else:
        body_color = tuple(int(x) for x in args.body.split(",")) if args.body else (80, 160, 255)
        eye_color = tuple(int(x) for x in args.eye.split(",")) if args.eye else (40, 40, 60)
        accent_color = tuple(int(x) for x in args.accent.split(",")) if args.accent else None
        creature_type = args.type

    generate_atlas(args.output, args.name, body_color, eye_color, accent_color, creature_type)


if __name__ == "__main__":
    main()
