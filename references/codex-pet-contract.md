# Codex Pet Atlas Contract

## Sprite Atlas Specification

| Property | Value |
|----------|-------|
| Grid | 8 columns x 9 rows |
| Frame size | 192 x 208 px |
| Atlas size | 1536 x 1872 px |
| Format | PNG (transparent background) |

## Animation States (Rows)

| Row | State | Description |
|-----|-------|-------------|
| 0 | idle | Standing idle, gentle breathing/swaying |
| 1 | running-right | Running toward the right |
| 2 | running-left | Running toward the left (mirror of row 1) |
| 3 | waving | Waving hand/greeting |
| 4 | jumping | Jumping up and down |
| 5 | failed | Sad/failed expression |
| 6 | waiting | Waiting, looking around |
| 7 | running | Running in place |
| 8 | review | Looking at code, inspecting |

## Frame Timing

- Each state has 8 frames
- Playback speed: ~100ms per frame (10 FPS)
- Idle and waiting states can be slower: ~150ms per frame

## pet.json Manifest

```json
{
  "name": "pet-name",
  "version": "1.0",
  "frame_width": 192,
  "frame_height": 208,
  "columns": 8,
  "states": [
    {"name": "idle", "row": 0, "frames": 8, "fps": 8},
    {"name": "running-right", "row": 1, "frames": 8, "fps": 10},
    {"name": "running-left", "row": 2, "frames": 8, "fps": 10},
    {"name": "waving", "row": 3, "frames": 8, "fps": 8},
    {"name": "jumping", "row": 4, "frames": 8, "fps": 10},
    {"name": "failed", "row": 5, "frames": 8, "fps": 6},
    {"name": "waiting", "row": 6, "frames": 8, "fps": 6},
    {"name": "running", "row": 7, "frames": 8, "fps": 10},
    {"name": "review", "row": 8, "frames": 8, "fps": 8}
  ]
}
```
