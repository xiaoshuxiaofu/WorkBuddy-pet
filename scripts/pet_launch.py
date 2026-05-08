"""
pet_launch.py - Smart launcher that starts daemon + pet if not already running.
Designed to be called from SessionStart hook.
"""
import os
import sys
import subprocess
import socket
import time

DAEMON_PORT = 19876
SKILL_DIR = os.path.join(os.path.expanduser("~"), ".codebuddy", "skills", "workbuddy-pet")
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
ATLAS = os.path.join(SKILL_DIR, "assets", "demo", "blue-slime_atlas.png")
MANIFEST = os.path.join(SKILL_DIR, "assets", "demo", "pet.json")


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


def launch():
    python = sys.executable

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

    # Start pet if not running (simple check: try connecting to daemon)
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
