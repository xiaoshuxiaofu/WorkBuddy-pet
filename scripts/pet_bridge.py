"""
pet_bridge.py - Ultra-lightweight CLI bridge to the pet daemon.
Usage:
    python pet_bridge.py thinking "正在思考..."
    python pet_bridge.py running "处理代码中..."
    python pet_bridge.py idle
    python pet_bridge.py status
"""
import sys
import json
import urllib.request

DAEMON_URL = "http://127.0.0.1:19876"

def main():
    if len(sys.argv) < 2:
        print("Usage: python pet_bridge.py <state> [message]")
        print("       python pet_bridge.py status")
        sys.exit(1)

    action = sys.argv[1]
    msg = sys.argv[2] if len(sys.argv) > 2 else ""

    if action == "status":
        resp = urllib.request.urlopen(f"{DAEMON_URL}/status")
        print(resp.read().decode("utf-8"))
        return

    data = json.dumps({"state": action, "message": msg}).encode("utf-8")
    req = urllib.request.Request(
        f"{DAEMON_URL}/set",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode("utf-8"))
    status = f"{result['state']}" + (f' "{result["message"]}"' if result.get("message") else "")
    print(status)

if __name__ == "__main__":
    main()
