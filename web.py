import os
import time
import threading
import requests
from flask import Flask

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE, "static"), static_url_path="/static")
STARTED = time.time()

@app.route("/")
def index():
    up = int(time.time() - STARTED)
    return f"OK - ticket bot alive ({up}s)", 200

@app.route("/health")
def health():
    return {"ok": True, "uptime": int(time.time() - STARTED)}, 200

@app.route("/ping")
def ping():
    return "pong", 200

def _self_ping_loop():
    time.sleep(30)
    while True:
        try:
            url = (os.getenv("KEEPALIVE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").strip()
            if url and not url.startswith("http"):
                url = "https://" + url
            if url:
                try:
                    requests.get(url.rstrip("/") + "/ping", timeout=15)
                    print("[keepalive] self ping sent (5min)")
                except Exception as e:
                    print(f"[keepalive] failed: {e}")
            time.sleep(300)
        except Exception as e:
            print(f"[keepalive] loop error: {e}")
            time.sleep(60)

def start_keepalive():
    if os.getenv("KEEPALIVE", "1") != "1":
        return
    t = threading.Thread(target=_self_ping_loop, daemon=True)
    t.start()

def run_web():
    port = int(os.getenv("PORT", "10000"))
    start_keepalive()
    app.run(host="0.0.0.0", port=port)

