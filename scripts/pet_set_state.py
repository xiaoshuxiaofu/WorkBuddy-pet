"""
Helper script to set pet chat state from CLI.
Usage:
    python pet_set_state.py thinking "正在思考中..."
    python pet_set_state.py idle
    python pet_set_state.py running "处理代码中..." --ctx-used 45000 --ctx-total 128000
"""
import os
import sys
import json
import time
import argparse

DEFAULT_STATE_FILE = os.path.join(os.path.expanduser("~"), ".workbuddy", "pet_state.json")

def main():
    parser = argparse.ArgumentParser(description="Set desktop pet chat state")
    parser.add_argument("state", help="State name (idle, thinking, running, etc.)")
    parser.add_argument("message", nargs="?", default="", help="Tooltip message")
    parser.add_argument("--ctx-used", type=int, default=None, help="Context tokens used")
    parser.add_argument("--ctx-total", type=int, default=None, help="Context tokens total")
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE, help="Path to pet_state.json")
    args = parser.parse_args()

    state_dir = os.path.dirname(args.state_file)
    os.makedirs(state_dir, exist_ok=True)

    # Read existing data to preserve context if not specified
    existing = {}
    if os.path.exists(args.state_file):
        try:
            with open(args.state_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass

    data = {
        "state": args.state,
        "message": args.message,
        "context_used": args.ctx_used if args.ctx_used is not None else existing.get("context_used", 0),
        "context_total": args.ctx_total if args.ctx_total is not None else existing.get("context_total", 128000),
        "timestamp": time.time(),
    }

    with open(args.state_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Pet state: {args.state}" + (f' "{args.message}"' if args.message else ""))

if __name__ == "__main__":
    main()
