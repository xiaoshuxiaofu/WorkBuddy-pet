"""
pet_daemon.py - Background bridge daemon for desktop pet state management.

Runs a lightweight HTTP server that the agent calls to update pet state during
conversations. Features:
- Auto-detection: watches WorkBuddy DB activity to infer agent state
- Auto-revert to idle after inactivity timeout
- Manual override via HTTP endpoints

Endpoints:
    GET /set?state=thinking&msg=Hello  →  set pet state with message
    GET /idle                            →  force idle immediately
    GET /status                          →  current state info
    GET /auto/enable                     →  enable auto-detection
    GET /auto/disable                    →  disable auto-detection

Usage:
    python pet_daemon.py [--port 19876] [--timeout 15] [--no-auto]

The daemon writes state to ~/.workbuddy/pet_state.json, which the desktop pet
polls every 500ms.
"""

import os
import sys
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DEFAULT_PORT = 19876
IDLE_TIMEOUT = 15  # seconds before auto-revert
STATE_FILE = os.path.join(os.path.expanduser("~"), ".workbuddy", "pet_state.json")
WORKBUDDY_DIR = os.path.join(os.path.expanduser("~"), ".workbuddy")

# Auto-detection timing
ACTIVITY_THRESHOLD = 2.0   # seconds: if session file modified within this window, agent is active
IDLE_THRESHOLD = 4.0       # seconds: if session file not modified for this long, agent is idle
WATCH_INTERVAL = 1.0       # seconds between checks
MANUAL_OVERRIDE_GRACE = 30  # seconds: after manual set, don't auto-override


def _find_session_file():
    """Find the current conversation transcript file."""
    projects_dir = os.path.join(WORKBUDDY_DIR, "projects")
    if not os.path.isdir(projects_dir):
        return None
    # Find the most recently modified .jsonl transcript file
    best = None
    best_mtime = 0
    for root, dirs, files in os.walk(projects_dir):
        for f in files:
            if f.endswith(".jsonl"):
                path = os.path.join(root, f)
                try:
                    mt = os.path.getmtime(path)
                    if mt > best_mtime:
                        best_mtime = mt
                        best = path
                except OSError:
                    pass
    return best


def _find_watch_targets():
    """Find the session transcript file to watch."""
    targets = []
    session_file = _find_session_file()
    if session_file:
        targets.append(session_file)
        print(f"[daemon] Watching session: {os.path.basename(session_file)}")
    # Fallback: also watch WAL if no session file found
    if not targets:
        wal = os.path.join(WORKBUDDY_DIR, "workbuddy.db-wal")
        if os.path.exists(wal):
            targets.append(wal)
            print("[daemon] Watching WAL (fallback)")
    return targets


def _get_latest_mtime(targets):
    """Get the most recent mtime among all watch targets."""
    latest = 0.0
    for target in targets:
        try:
            if os.path.isfile(target):
                mtime = os.path.getmtime(target)
                if mtime > latest:
                    latest = mtime
        except OSError:
            pass
    return latest


class PetDaemon:
    def __init__(self, timeout: int = IDLE_TIMEOUT, auto_detect: bool = True):
        self.timeout = timeout
        self.current_state = "idle"
        self.current_message = ""
        self.last_update = time.time()
        self.manual_override_until = 0.0  # timestamp until manual override is active
        self.auto_detect = auto_detect
        self.lock = threading.Lock()
        self._stop_event = threading.Event()

        # Watch targets for activity detection
        self._watch_targets = _find_watch_targets()
        print(f"[daemon] Watching {len(self._watch_targets)} targets for activity")

        # Start auto-revert thread
        self._revert_thread = threading.Thread(target=self._auto_revert_loop, daemon=True)
        self._revert_thread.start()

        # Start activity watcher thread
        if self.auto_detect:
            self._watch_thread = threading.Thread(target=self._activity_watch_loop, daemon=True)
            self._watch_thread.start()
            print("[daemon] Auto-detection enabled")

    def set_state(self, state: str, message: str = "", manual: bool = False):
        """Set pet state and write to state file."""
        with self.lock:
            self.current_state = state
            self.current_message = message
            self.last_update = time.time()
            if manual:
                self.manual_override_until = time.time() + MANUAL_OVERRIDE_GRACE
            self._write_state_file(state, message)

    def _write_state_file(self, state: str, message: str):
        """Write state to the pet state file."""
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "state": state,
                    "message": message,
                    "timestamp": time.time(),
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[daemon] Failed to write state file: {e}", file=sys.stderr)

    def get_status(self) -> dict:
        """Get current daemon status."""
        with self.lock:
            elapsed = time.time() - self.last_update
            return {
                "state": self.current_state,
                "message": self.current_message,
                "seconds_since_update": round(elapsed, 1),
                "timeout": self.timeout,
                "auto_detect": self.auto_detect,
            }

    def _should_auto_detect(self) -> bool:
        """Check if auto-detection should be active (not overridden)."""
        return self.auto_detect and time.time() > self.manual_override_until

    def _activity_watch_loop(self):
        """Background thread: watch session file and auto-set thinking."""
        rescan_counter = 0
        while not self._stop_event.is_set():
            try:
                # Periodically rescan for latest session file
                rescan_counter += 1
                if rescan_counter >= 30:  # Every 30s
                    rescan_counter = 0
                    new_targets = _find_watch_targets()
                    if new_targets and new_targets != self._watch_targets:
                        self._watch_targets = new_targets

                if not self._watch_targets:
                    self._stop_event.wait(WATCH_INTERVAL)
                    continue

                latest = _get_latest_mtime(self._watch_targets)
                now = time.time()

                with self.lock:
                    if not self._should_auto_detect():
                        pass  # Manual override active, skip
                    elif now - latest < ACTIVITY_THRESHOLD:
                        # Recent activity detected → agent is working
                        if self.current_state == "idle":
                            self.current_state = "thinking"
                            self.current_message = "正在思考..."
                            self.last_update = now
                            self._write_state_file("thinking", "正在思考...")
                    elif (now - latest > IDLE_THRESHOLD and
                          self.current_state == "thinking" and
                          now - self.last_update > IDLE_THRESHOLD):
                        # No recent activity → agent is idle
                        self.current_state = "idle"
                        self.current_message = ""
                        self.last_update = now
                        self._write_state_file("idle", "")
            except Exception:
                pass

            self._stop_event.wait(WATCH_INTERVAL)

    def _auto_revert_loop(self):
        """Background thread: auto-revert to idle after timeout (safety net)."""
        while not self._stop_event.is_set():
            with self.lock:
                if (self.current_state != "idle" and
                        time.time() - self.last_update > self.timeout):
                    print(f"[daemon] Auto-revert: {self.current_state} → idle")
                    self.current_state = "idle"
                    self.current_message = ""
                    self._write_state_file("idle", "")
            self._stop_event.wait(2)

    def shutdown(self):
        """Shutdown the daemon."""
        self._stop_event.set()
        self.set_state("idle", "")


class PetHandler(BaseHTTPRequestHandler):
    daemon: PetDaemon = None

    def log_message(self, format, *args):
        pass

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        fixed_params = {}
        for k, v_list in params.items():
            fixed_params[k] = [
                v.encode("latin-1").decode("utf-8") for v in v_list
            ]

        if path in ("", "/", "/status"):
            self._send_json(self.daemon.get_status())

        elif path == "/set":
            state = fixed_params.get("state", [""])[0]
            msg = fixed_params.get("msg", [""])[0]
            if not state:
                self._send_json({"error": "Missing 'state' parameter"}, 400)
                return
            self.daemon.set_state(state, msg, manual=True)
            self._send_json({"ok": True, "state": state, "message": msg})

        elif path == "/idle":
            self.daemon.set_state("idle", "", manual=True)
            self._send_json({"ok": True, "state": "idle"})

        elif path == "/auto/enable":
            self.daemon.auto_detect = True
            self._send_json({"ok": True, "auto_detect": True})

        elif path == "/auto/disable":
            self.daemon.auto_detect = False
            self._send_json({"ok": True, "auto_detect": False})

        else:
            self._send_json({"error": "Unknown endpoint"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        if path in ("/set", "/state"):
            state = data.get("state", "")
            msg = data.get("message", data.get("msg", ""))
            if not state:
                self._send_json({"error": "Missing 'state'"}, 400)
                return
            self.daemon.set_state(state, msg, manual=True)
            self._send_json({"ok": True, "state": state, "message": msg})
        elif path == "/idle":
            self.daemon.set_state("idle", "", manual=True)
            self._send_json({"ok": True, "state": "idle"})
        else:
            self._send_json({"error": "Unknown endpoint"}, 404)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pet state daemon")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=int, default=IDLE_TIMEOUT)
    parser.add_argument("--no-auto", action="store_true", help="Disable auto-detection")
    args = parser.parse_args()

    daemon = PetDaemon(timeout=args.timeout, auto_detect=not args.no_auto)

    PetHandler.daemon = daemon

    server = HTTPServer(("127.0.0.1", args.port), PetHandler)
    print(f"[daemon] Pet bridge running on http://127.0.0.1:{args.port}")
    print(f"[daemon] Auto-revert timeout: {args.timeout}s")
    print(f"[daemon] Auto-detect: {'ON' if daemon.auto_detect else 'OFF'}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[daemon] Shutting down...")
        daemon.shutdown()
        server.shutdown()


if __name__ == "__main__":
    main()
