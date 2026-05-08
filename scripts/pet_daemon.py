"""
pet_daemon.py - Background bridge daemon for desktop pet state management.

Runs a lightweight HTTP server that receives state commands from hooks/manual use.
State changes are written to ~/.workbuddy/pet_state.json, which the desktop pet
polls every 500ms. State persists until explicitly changed (no auto-revert).

Endpoints:
    POST /set     {"state": "thinking", "message": "正在思考..."}  →  set pet state
    GET  /set?state=thinking&msg=Hello                            →  set pet state (GET form)
    POST /idle                                                       →  force idle
    GET  /idle                                                       →  force idle
    GET  /status                                                     →  current state info

Usage:
    python pet_daemon.py [--port 19876]
"""

import os
import sys
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DEFAULT_PORT = 19876
STATE_FILE = os.path.join(os.path.expanduser("~"), ".workbuddy", "pet_state.json")


class PetDaemon:
    def __init__(self):
        self.current_state = "idle"
        self.current_message = ""
        self.last_update = time.time()
        self.lock = threading.Lock()
        self._stop_event = threading.Event()

    def set_state(self, state: str, message: str = ""):
        with self.lock:
            self.current_state = state
            self.current_message = message
            self.last_update = time.time()
            self._write_state_file(state, message)

    def _write_state_file(self, state: str, message: str):
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
        with self.lock:
            elapsed = time.time() - self.last_update
            return {
                "state": self.current_state,
                "message": self.current_message,
                "seconds_since_update": round(elapsed, 1),
            }

    def shutdown(self):
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
            self.daemon.set_state(state, msg)
            self._send_json({"ok": True, "state": state, "message": msg})

        elif path == "/idle":
            self.daemon.set_state("idle", "")
            self._send_json({"ok": True, "state": "idle"})

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
            self.daemon.set_state(state, msg)
            self._send_json({"ok": True, "state": state, "message": msg})
        elif path == "/idle":
            self.daemon.set_state("idle", "")
            self._send_json({"ok": True, "state": "idle"})
        else:
            self._send_json({"error": "Unknown endpoint"}, 404)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pet state daemon")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    daemon = PetDaemon()
    PetHandler.daemon = daemon

    server = HTTPServer(("127.0.0.1", args.port), PetHandler)
    print(f"[daemon] Pet bridge running on http://127.0.0.1:{args.port}")

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
