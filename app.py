import os
import threading
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
    import bot_cmds
    token = os.getenv("DISCORD_TOKEN", "")
    bot_cmds.run_bot(token)


def _ensure_bot():
    t = threading.Thread(target=_run_bot, daemon=True)
    t.start()
    return t


BOT_THREAD = _ensure_bot()
start_keepalive()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

