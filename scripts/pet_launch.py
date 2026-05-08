"""
pet_launch.py - Smart launcher that starts daemon + pet if not already running.
Designed to be called from SessionStart hook.

On first launch, automatically installs hooks into ~/.workbuddy/settings.json.
"""
import os
import sys
import subprocess
import socket
import time

DAEMON_PORT = 19876
SKILL_DIR = os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", "workbuddy-pet")
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
ATLAS = os.path.join(SKILL_DIR, "assets", "demo", "blue-slime_atlas.png")
MANIFEST = os.path.join(SKILL_DIR, "assets", "demo", "pet.json")
HOOKS_MARKER = os.path.join(os.path.expanduser("~"), ".workbuddy", ".pet-hooks-installed")


def daemon_alive():
    """Check if daemon is running on its port."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", DAEMON_PORT))
        s.close()
        return True
    except Exception:
        return False


def ensure_hooks_installed():
    """Run install_hooks.py to register hooks in settings.json (idempotent)."""
    install_script = os.path.join(SCRIPTS_DIR, "install_hooks.py")
    if os.path.exists(install_script):
        try:
            result = subprocess.run(
                [sys.executable, install_script],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                # Create marker file so we don't spam logs
                os.makedirs(os.path.dirname(HOOKS_MARKER), exist_ok=True)
                with open(HOOKS_MARKER, "w") as f:
                    f.write(str(time.time()))
            else:
                print(f"[launch] Hook install warning: {result.stderr.strip()}")
        except Exception as e:
            print(f"[launch] Hook install skipped: {e}")


def launch():
    python = sys.executable

    # Ensure hooks are installed (idempotent, fast)
    ensure_hooks_installed()

    # Start daemon if not running
    if daemon_alive():
        print("[launch] Daemon already running")
    else:
        print("[launch] Starting daemon...")
        subprocess.Popen(
            [python, os.path.join(SCRIPTS_DIR, "pet_daemon.py")],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        time.sleep(1)

    # Start pet
    print("[launch] Starting pet...")
    subprocess.Popen(
        [
            python,
            os.path.join(SCRIPTS_DIR, "desktop_pet.py"),
            "--atlas", ATLAS,
            "--manifest", MANIFEST,
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    print("[launch] Done")


if __name__ == "__main__":
    launch()
