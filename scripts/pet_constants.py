"""
pet_constants.py - Shared constants for the WorkBuddy pet system.
"""
import os

# ── Sprite atlas dimensions ──
FRAME_WIDTH = 192
FRAME_HEIGHT = 208
COLUMNS = 8
ROWS = 9

# ── Animation ──
DEFAULT_FPS = 10
WANDER_INTERVAL = 5000       # ms between wander actions
WANDER_STEP = 60              # pixels per wander step
STATE_POLL_INTERVAL = 150    # ms between state file checks

# ── State names (row order in atlas) ──
STATE_NAMES = [
    "idle", "running-right", "running-left", "waving",
    "jumping", "failed", "waiting", "running", "review",
]

# ── State aliases: chat-state → animation-state ──
STATE_ALIASES = {
    "thinking":   "waiting",
    "coding":     "running",
    "debugging":  "failed",
    "reading":    "review",
    "writing":    "running",
    "searching":  "running-right",
    "agree":      "waving",   # 请求同意 → 挥手状态 + 特别按钮
}

# ── State labels (Chinese) ──
STATE_LABELS = {
    "idle":          "待机",
    "running-right": "向右跑",
    "running-left":  "向左跑",
    "waving":        "挥手/完成",
    "jumping":       "跳跃",
    "failed":        "失败",
    "waiting":       "思考中",
    "running":       "工作中",
    "review":        "审查代码",
}

# ── File paths ──
STATE_FILE = os.path.join(os.path.expanduser("~"), ".workbuddy", "pet_state.json")
PET_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".workbuddy", "pet_config.json")
DAEMON_PORT = 19876

# ── Pixel bubble styling ──
BUBBLE_BG = "#f8f8f0"
BUBBLE_BORDER = "#3a3a3a"
BUBBLE_TEXT = "#3a3a3a"
BUBBLE_PAD_X = 8
BUBBLE_PAD_Y = 4
BUBBLE_ARROW_H = 6
