"""
pet_launch.py - Smart launcher that starts daemon + pet if not already running.
Designed to be called from SessionStart hook.

On first launch, automatically installs hooks into ~/.workbuddy/settings.json.
Reads active pet from pet_config.json to remember last selection.
"""
import os
import sys
import json
import subprocess
import socket
import time

DAEMON_PORT = 19876
SKILL_DIR = os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", "workbuddy-pet")
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
ASSETS_DIR = os.path.join(SKILL_DIR, "assets")
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".workbuddy", "pet_config.json")
HOOKS_MARKER = os.path.join(os.path.expanduser("~"), ".workbuddy", ".pet-hooks-installed")


def get_active_pet() -> tuple[str, str]:
    """Return (atlas_path, manifest_path) for the active pet. Falls back to diana."""
    pet_name = "diana"

    # Try reading saved preference
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            pet_name = config.get("active_pet", "diana")
    except (OSError, json.JSONDecodeError):
        pass

    # Try the saved pet
    atlas = os.path.join(ASSETS_DIR, pet_name, f"{pet_name}_atlas.png")
    manifest = os.path.join(ASSETS_DIR, pet_name, "pet.json")
    if os.path.exists(atlas) and os.path.exists(manifest):
        return atlas, manifest

    # Fallback: scan for any available pet
    try:
        for entry in sorted(os.listdir(ASSETS_DIR)):
            pet_dir = os.path.join(ASSETS_DIR, entry)
            if not os.path.isdir(pet_dir):
                continue
            atlas = os.path.join(pet_dir, f"{entry}_atlas.png")
            manifest = os.path.join(pet_dir, "pet.json")
            if os.path.exists(atlas) and os.path.exists(manifest):
                return atlas, manifest
    except OSError:
        pass

    # Absolute last resort: hardcoded diana
    return (os.path.join(ASSETS_DIR, "diana", "diana_atlas.png"),
            os.path.join(ASSETS_DIR, "diana", "pet.json"))


def _popen_kwargs():
    """Return platform-appropriate Popen kwargs (hide window on Windows)."""
    if sys.platform == "win32":
        try:
            return {"creationflags": subprocess.CREATE_NO_WINDOW}
        except AttributeError:
            pass
    return {}


def daemon_alive():
    """Check if daemon is running on its port."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", DAEMON_PORT))
        s.close()
        return True
    except OSError:
        return False


def ensure_hooks_installed():
    """Run install_hooks.py to register hooks in settings.json (idempotent)."""
    install_script = os.path.join(SCRIPTS_DIR, "install_hooks.py")
    if not os.path.exists(install_script):
        return
    try:
        result = subprocess.run(
            [sys.executable, install_script],
            capture_output=True, text=True, timeout=10, **_popen_kwargs(),
        )
        if result.returncode == 0:
            os.makedirs(os.path.dirname(HOOKS_MARKER), exist_ok=True)
            with open(HOOKS_MARKER, "w") as f:
                f.write(str(time.time()))
        else:
            print(f"[launch] Hook install warning: {result.stderr.strip()}")
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[launch] Hook install skipped: {e}")


def launch():
    python = sys.executable
    popen_kw = _popen_kwargs()
    atlas, manifest = get_active_pet()

    ensure_hooks_installed()

    if daemon_alive():
        print("[launch] Daemon already running")
    else:
        print("[launch] Starting daemon...")
        subprocess.Popen(
            [python, os.path.join(SCRIPTS_DIR, "pet_daemon.py")], **popen_kw,
        )
        time.sleep(1)

    print("[launch] Starting pet...")
    subprocess.Popen(
        [python, os.path.join(SCRIPTS_DIR, "desktop_pet.py"),
         "--atlas", atlas, "--manifest", manifest, "--scale", "1.0"], **popen_kw,
    )
    print("[launch] Done")


if __name__ == "__main__":
    launch()
