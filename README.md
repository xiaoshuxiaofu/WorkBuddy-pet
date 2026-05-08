# Codex Pet - Desktop Pet Generator & Player for WorkBuddy

Generate Codex-style sprite atlas pets and display them as desktop companions.

## Quick Start

### Run the demo pet (Blue Slime)
```bash
cd codex-pet
python scripts/desktop_pet.py --atlas output/pets/demo/blue-slime_atlas.png --manifest output/pets/demo/pet.json --scale 2.0
```

Or simply double-click `launch_pet.bat` on Windows.

### Generate a new demo pet
```bash
python scripts/generate_demo_atlas.py --output ./output/pets/mypet --name my-pet
```

## Controls

| Action | How |
|--------|-----|
| Drag pet | Left-click + drag |
| Switch state | Double-click (cycles through states) |
| Context menu | Right-click |
| Quit | Right-click → Exit |

## Animation States

| State | Description |
|-------|-------------|
| idle | Standing idle, gentle breathing |
| running-right | Running toward the right |
| running-left | Running toward the left |
| waving | Waving hand |
| jumping | Jumping up and down |
| failed | Sad expression |
| waiting | Looking around |
| running | Running in place |
| review | Inspecting code |

## Scripts

| Script | Purpose |
|--------|---------|
| `desktop_pet.py` | Tkinter desktop pet player |
| `generate_demo_atlas.py` | Generate demo pixel-art sprite atlas |
| `compose_atlas.py` | Compose atlas from individual frames |
| `extract_strip_frames.py` | Extract frames from strip images |
| `validate_atlas.py` | Validate atlas against spec |
| `make_contact_sheet.py` | Generate thumbnail grid |

## Sprite Atlas Spec

- Grid: 8 columns x 9 rows
- Frame size: 192 x 208 px
- Atlas size: 1536 x 1872 px
- Format: PNG with transparent background
