import os
import threading
import traceback
from dotenv import load_dotenv
import store
from web import app, start_keepalive
from dash_api import dash, dashboard_page

load_dotenv()
store.init_storage()
app.register_blueprint(dash)


@app.route("/dashboard")
def dashboard():
    return dashboard_page()


def _run_bot():
    try:
        import bot_cmds
    except Exception:
        print("[bot] import failed:")
        traceback.print_exc()
        return
    token = os.getenv("DISCORD_TOKEN", "")
    try:
        bot_cmds.run_bot(token)
    except Exception:
        print("[bot] run failed:")
        traceback.print_exc()


def _ensure_bot():
    t = threading.Thread(target=_run_bot, daemon=True)
    t.start()
    return t


BOT_THREAD = _ensure_bot()
start_keepalive()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

