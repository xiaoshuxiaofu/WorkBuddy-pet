"""
install_hooks.py - 将 pet hooks 注入到 ~/.workbuddy/settings.json。

读取同目录下 hooks.json 的配置，合并到 settings.json 的 "hooks" 字段中。
幂等操作：重复运行不会产生重复条目。

Usage:
    python install_hooks.py
    python install_hooks.py --skill-dir /path/to/workbuddy-pet
    python install_hooks.py --uninstall  # 移除 pet hooks
"""

import os
import sys
import json
import argparse

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".workbuddy", "settings.json")

# 用于识别已注入的 pet hooks 的标记
_HOOK_MARKER = "workbuddy-pet"


def load_json(path: str) -> dict:
    """Load JSON file, return empty dict if not exists."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path: str, data: dict):
    """Save JSON file with indent."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_skill_dir(args) -> str:
    """Determine skill directory."""
    if args.skill_dir:
        return args.skill_dir
    # 如果从 skill 的 scripts/ 子目录运行，向上一级
    if os.path.basename(SKILL_DIR) == "scripts":
        return os.path.dirname(SKILL_DIR)
    return SKILL_DIR


def load_skill_hooks(skill_dir: str) -> dict:
    """Load hooks.json from skill directory."""
    hooks_path = os.path.join(skill_dir, "hooks.json")
    if not os.path.exists(hooks_path):
        print(f"[install] hooks.json not found at {hooks_path}")
        return {}
    with open(hooks_path, "r", encoding="utf-8") as f:
        return json.load(f).get("hooks", {})


def hooks_match(existing: dict, new_hook: dict) -> bool:
    """Check if two hook entries are effectively the same."""
    if existing.get("type") != new_hook.get("type"):
        return False
    if existing.get("command") == new_hook.get("command"):
        return True
    if existing.get("prompt") == new_hook.get("prompt"):
        return True
    return False


def install(args):
    """Install pet hooks into settings.json."""
    skill_dir = get_skill_dir(args)
    skill_hooks = load_skill_hooks(skill_dir)
    if not skill_hooks:
        print("[install] No hooks to install.")
        return False

    settings = load_json(SETTINGS_FILE)
    settings_hooks = settings.get("hooks", {})

    # Track if any changes were made
    changed = False

    for event_name, event_entries in skill_hooks.items():
        if event_name not in settings_hooks:
            # Add marker comment and hooks
            settings_hooks[event_name] = event_entries
            changed = True
            print(f"[install] Added {len(event_entries)} hook entry(s) for {event_name}")
        else:
            # Merge: check for duplicates
            for new_entry in event_entries:
                matcher = new_entry.get("matcher", "")
                existing_list = settings_hooks[event_name]
                is_dup = False
                for ex in existing_list:
                    if ex.get("matcher", "") == matcher:
                        # Same matcher, check if hooks are already there
                        for new_h in new_entry.get("hooks", []):
                            for ex_h in ex.get("hooks", []):
                                if hooks_match(ex_h, new_h):
                                    is_dup = True
                                    break
                        if is_dup:
                            break
                if not is_dup:
                    existing_list.append(new_entry)
                    changed = True
                    print(f"[install] Added hook entry for {event_name} (matcher: {matcher or '*'})")

    if changed:
        settings["hooks"] = settings_hooks
        save_json(SETTINGS_FILE, settings)
        print(f"[install] Hooks saved to {SETTINGS_FILE}")
        print("[install] Please restart WorkBuddy or reload hooks for changes to take effect.")
    else:
        print("[install] All hooks already installed, no changes needed.")

    return True


def uninstall(args):
    """Remove pet hooks from settings.json."""
    settings = load_json(SETTINGS_FILE)
    settings_hooks = settings.get("hooks", {})
    changed = False

    for event_name in list(settings_hooks.keys()):
        entries = settings_hooks[event_name]
        # Filter out entries that reference workbuddy-pet scripts
        filtered = []
        for entry in entries:
            hooks_list = entry.get("hooks", [])
            is_pet = False
            for h in hooks_list:
                cmd = h.get("command", "")
                if _HOOK_MARKER in cmd:
                    is_pet = True
                    break
            if not is_pet:
                filtered.append(entry)
            else:
                changed = True
                print(f"[uninstall] Removed hook entry from {event_name}")
        settings_hooks[event_name] = filtered
        # Remove empty event arrays
        if not filtered:
            del settings_hooks[event_name]

    if changed:
        settings["hooks"] = settings_hooks
        save_json(SETTINGS_FILE, settings)
        print(f"[uninstall] Hooks removed from {SETTINGS_FILE}")
    else:
        print("[uninstall] No pet hooks found, nothing to remove.")

    return True


def main():
    parser = argparse.ArgumentParser(description="Install/uninstall workbuddy-pet hooks")
    parser.add_argument("--skill-dir", help="Path to workbuddy-pet skill directory")
    parser.add_argument("--uninstall", action="store_true", help="Remove pet hooks from settings")
    args = parser.parse_args()

    if args.uninstall:
        success = uninstall(args)
    else:
        success = install(args)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
