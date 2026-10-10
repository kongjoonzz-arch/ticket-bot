import os
import uuid
from functools import wraps
from flask import Blueprint, request, jsonify
import store

dash = Blueprint("dash", __name__)

def _pw():
    return os.getenv("DASHBOARD_PASSWORD", "admin1234")

def _check(f):
    @wraps(f)
    def w(*a, **kw):
        pw = request.headers.get("X-Admin-PW") or request.args.get("pw") or request.form.get("pw")
        if pw != _pw():
            return jsonify({"ok": False, "error": "unauthorized"}), 401
        return f(*a, **kw)
    return w

@dash.route("/api/auth", methods=["POST"])
def api_auth():
    data = request.get_json(force=True, silent=True) or {}
    pw = data.get("pw") or request.headers.get("X-Admin-PW")
    if pw == _pw():
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 401

@dash.route("/api/products", methods=["GET"])
@_check
def api_products():
    return jsonify({"ok": True, "products": store.load_products()})

@dash.route("/api/products", methods=["POST"])
@_check
def api_products_save():
    data = request.get_json(force=True, silent=True) or {}
    prods = data.get("products", [])
    out = []
    for p in prods:
        pid = str(p.get("id") or uuid.uuid4().hex[:8])
        try:
            price = int(p.get("price", 0))
        except Exception:
            price = 0
        try:
            stock = int(p.get("stock", 0))
        except Exception:
            stock = 0
        out.append({"id": pid, "name": str(p.get("name", "product"))[:100], "price": price, "stock": stock, "description": str(p.get("description", ""))[:500], "enabled": bool(p.get("enabled", True))})
    store.save_products(out)
    return jsonify({"ok": True, "products": out})

@dash.route("/api/questions", methods=["GET"])
@_check
def api_questions():
    return jsonify({"ok": True, "questions": store.load_questions()})

@dash.route("/api/questions", methods=["POST"])
@_check
def api_questions_save():
    data = request.get_json(force=True, silent=True) or {}
    q = {"buy": [], "error": []}
    for kind in ("buy", "error"):
        for i, item in enumerate(data.get(kind, [])[:5]):
            try:
                ml = int(item.get("max_length", 200) or 200)
            except Exception:
                ml = 200
            q[kind].append({"id": str(item.get("id") or "%s%d" % (kind, i + 1)), "label": str(item.get("label", "Q"))[:45], "placeholder": str(item.get("placeholder", ""))[:100], "required": bool(item.get("required", True)), "max_length": ml, "enabled": bool(item.get("enabled", True))})
    store.save_questions(q)
    return jsonify({"ok": True, "questions": q})

@dash.route("/api/settings", methods=["GET"])
@_check
def api_settings():
    return jsonify({"ok": True, "settings": store.load_settings()})

@dash.route("/api/settings", methods=["POST"])
@_check
def api_settings_save():
    data = request.get_json(force=True, silent=True) or {}
    cur = store.load_settings()
    for k in cur.keys():
        if k in data:
            cur[k] = data[k]
    try:
        cur["panel_color"] = int(cur.get("panel_color", 0x5865F2))
    except Exception:
        cur["panel_color"] = 0x5865F2
    v = cur.get("mention_admin_on_create", True)
    if isinstance(v, str):
        v = v.lower() == "true"
    cur["mention_admin_on_create"] = bool(v)
    store.save_settings(cur)
    return jsonify({"ok": True, "settings": cur})

@dash.route("/api/tickets", methods=["GET"])
@_check
def api_tickets():
    return jsonify({"ok": True, "tickets": store.load_tickets()})

@dash.route("/api/notices", methods=["GET"])
@_check
def api_notices():
    return jsonify({"ok": True, "notices": store.load_notices()})

@dash.route("/api/announce", methods=["POST"])
@_check
def api_announce_preview():
    data = request.get_json(force=True, silent=True) or {}
    s = store.load_settings()
    keys = ["announce_channel_id", "announce_title", "announce_message",
            "announce_color", "announce_image_url", "announce_footer",
            "announce_mention", "announce_mention_role_id"]
    for k in keys:
        if k in data:
            s[k] = data[k]
    try:
        color = int(s.get("announce_color", 0x5865F2))
    except Exception:
        color = 0x5865F2
    preview = {"title": str(s.get("announce_title", ""))[:256],
               "message": str(s.get("announce_message", ""))[:4000],
               "color": color,
               "image": str(s.get("announce_image_url", "") or ""),
               "footer": str(s.get("announce_footer", "") or ""),
               "mention": str(s.get("announce_mention", "none")),
               "channel_id": str(s.get("announce_channel_id", "") or "")}
    do_save = bool(data.get("save", True))
    if do_save:
        store.save_settings(s)
    return jsonify({"ok": True, "preview": preview, "settings": s})

def dashboard_page():
    base = os.path.dirname(os.path.abspath(__file__))
    for name in ("dash_pro.html",):
        path = os.path.join(base, "templates", name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    return "dashboard template missing"


