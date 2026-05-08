---
name: workbuddy-pet
description: Desktop pet generator and player for WorkBuddy. This skill should be used when users want to create, customize, or launch a desktop pet companion. Triggers on requests like "hatch a pet", "launch desktop pet", "create a pet", "show me the pet", or any mention of desktop companions/pets.
agent_created: true
---

# WorkBuddy Pet

## Overview

Generate Codex-compatible sprite atlas pets and display them as desktop companions using a tkinter transparent window. The pet supports 9 animation states, drag-to-move, right-click menu, double-click state cycling, and auto-wander mode.

## Quick Start

Launch the default blue-slime pet:

```bash
python <SKILL_DIR>/scripts/desktop_pet.py --atlas <SKILL_DIR>/assets/demo/blue-slime_atlas.png --manifest <SKILL_DIR>/assets/demo/pet.json --scale 2.0
```

On Windows, can also use:

```powershell
python "<SKILL_DIR>/scripts/desktop_pet.py" --atlas "<SKILL_DIR>/assets/demo/blue-slime_atlas.png" --manifest "<SKILL_DIR>/assets/demo/pet.json" --scale 2.0
```

## Core Capabilities

### 1. Launch Desktop Pet

Run `desktop_pet.py` with a sprite atlas and optional manifest file. The pet appears as a borderless, transparent, always-on-top window at the bottom-right of the screen.

**Parameters:**
- `--atlas` (required): Path to sprite atlas PNG
- `--manifest` (optional): Path to pet.json manifest
- `--scale` (optional): Display scale factor, default 2.0

**Controls:**
| Action | How |
|--------|-----|
| Drag pet | Left-click + drag |
| Switch state | Double-click (cycles through states) |
| Context menu | Right-click (state selection, wander toggle, exit) |

### 2. Generate Demo Pet Atlas

Create a procedurally-generated pixel-art blue slime sprite atlas:

```bash
python <SKILL_DIR>/scripts/generate_demo_atlas.py --output <output_dir> --name <pet_name>
```

### 3. Compose Custom Atlas from Frames

If individual frame images are available (e.g. from AI image generation), compose them into a sprite atlas:

```bash
python <SKILL_DIR>/scripts/compose_atlas.py --input-dir <frames_dir> --output <atlas.png> --name <pet_name>
```

Expected input structure:
```
frames_dir/
    idle/           frame_0.png ... frame_7.png
    running-right/  frame_0.png ... frame_7.png
    running-left/   frame_0.png ... frame_7.png
    waving/         frame_0.png ... frame_7.png
    jumping/        frame_0.png ... frame_7.png
    failed/         frame_0.png ... frame_7.png
    waiting/        frame_0.png ... frame_7.png
    running/        frame_0.png ... frame_7.png
    review/         frame_0.png ... frame_7.png
```

### 4. Validate Atlas

Check if a sprite atlas meets the Codex Pet specification:

```bash
python <SKILL_DIR>/scripts/validate_atlas.py --atlas <atlas.png> --manifest <pet.json>
```

### 5. Generate Contact Sheet

Create a thumbnail grid overview of the sprite atlas:

```bash
python <SKILL_DIR>/scripts/make_contact_sheet.py --atlas <atlas.png> --output <contact.png>
```

## Sprite Atlas Specification

| Property | Value |
|----------|-------|
| Grid | 8 columns x 9 rows |
| Frame size | 192 x 208 px |
| Atlas size | 1536 x 1872 px |
| Format | PNG with transparent background |

### Animation States

| Row | State | Description | FPS |
|-----|-------|-------------|-----|
| 0 | idle | Standing idle, gentle breathing | 8 |
| 1 | running-right | Running toward the right | 10 |
| 2 | running-left | Running toward the left | 10 |
| 3 | waving | Waving hand/greeting | 8 |
| 4 | jumping | Jumping up and down | 10 |
| 5 | failed | Sad/failed expression | 6 |
| 6 | waiting | Looking around, waiting | 6 |
| 7 | running | Running in place | 10 |
| 8 | review | Inspecting code | 8 |

## Dependencies

- Python 3.10+
- Pillow (`pip install Pillow`)
- tkinter (included with standard Python on Windows/macOS)
