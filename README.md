# WorkBuddy Pet - Desktop Pet for WorkBuddy

Generate Codex-style sprite atlas pets and display them as desktop companions. Supports chat-aware mode with hooks-driven state sync.

## Quick Start

### Run the demo pet (Blue Slime)
```bash
# Recommended: one-click launch (daemon + pet)
python scripts/pet_launch.py

# Or manual (debugging):
python scripts/desktop_pet.py --atlas assets/demo/blue-slime_atlas.png --manifest assets/demo/pet.json --scale 2.0
```

> **Important**: `desktop_pet.py` requires `--atlas` parameter. Use `pet_launch.py` for normal startup.

### Restart the pet
```bash
taskkill /F /IM python.exe
python scripts/pet_launch.py
```

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
| `pet_launch.py` | **Primary launcher** — starts daemon + pet with correct args |
| `desktop_pet.py` | Tkinter desktop pet player (requires --atlas) |
| `pet_daemon.py` | HTTP daemon for state management |
| `pet_bridge.py` | CLI to control pet state manually |
| `install_hooks.py` | Install/uninstall WorkBuddy hooks |
| `generate_demo_atlas.py` | Generate demo pixel-art sprite atlas |
| `compose_atlas.py` | Compose atlas from individual frames |
| `validate_atlas.py` | Validate atlas against spec |
| `make_contact_sheet.py` | Generate thumbnail grid |

## Chat-Aware Mode

The pet syncs with WorkBuddy AI agent state via hooks:

| Hook | Pet State | Bubble |
|------|-----------|--------|
| UserPromptSubmit | thinking | "正在思考..." |
| PostToolUse | running | "工作中..." |
| Stop | waving | "完成！" + sound |
| SessionEnd | idle | — |

- Sound plays only on completion (waving state)
- Sound toggle in right-click menu, persisted to `~/.workbuddy/pet_config.json`

## Sprite Atlas Spec

- Grid: 8 columns x 9 rows
- Frame size: 192 x 208 px
- Atlas size: 1536 x 1872 px
- Format: PNG with transparent background
