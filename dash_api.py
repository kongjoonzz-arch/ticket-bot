import os
import uuid
from functools import wraps
from flask import Blueprint, request, jsonify
import store

dash = Blueprint("dash", __name__)


def _int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

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
    return jsonify({"ok": True, "products": store.load_products(),
                    "categories": store.load_category_order()})

@dash.route("/api/products", methods=["POST"])
@_check
def api_products_save():
    data = request.get_json(force=True, silent=True) or {}
    prods = data.get("products", [])
    old = {str(p.get("id")): p for p in store.load_products()}
    out = []
    for i, p in enumerate(prods):
        pid = str(p.get("id") or uuid.uuid4().hex[:8])
        try:
            price = int(p.get("price", 0))
        except Exception:
            price = 0
        try:
            stock = int(p.get("stock", 0))
        except Exception:
            stock = 0
        try:
            qty = int(p.get("quantity", 1) or 1)
        except Exception:
            qty = 1
        try:
            disc = int(p.get("discount", 0) or 0)
        except Exception:
            disc = 0
        try:
            order = int(p.get("order", i + 1) or (i + 1))
        except Exception:
            order = i + 1
        out.append({"id": pid, "name": str(p.get("name", "product"))[:100],
                    "category": str(p.get("category", "") or "").strip()[:60],
                    "price": price, "quantity": max(1, qty), "discount": max(0, disc),
                    "stock": stock, "order": order,
                    "description": str(p.get("description", ""))[:500],
                    "enabled": bool(p.get("enabled", True))})
    store.save_products(out)
    # 재고가 늘어난 상품 → 입고 알림
    added = []
    for p in out:
        prev = old.get(str(p["id"]))
        if not prev:
            continue
        before = _int(prev.get("stock"), 0)
        after = _int(p.get("stock"), 0)
        if before >= 0 and after > before:
            added.append({"name": p["name"], "category": p.get("category"),
                          "added": after - before, "stock": after})
    if added:
        try:
            import ui_stock
            ui_stock.send_restock(store.load_settings(), added, source="대시보드 재고 수정")
        except Exception as e:
            print(f"[stock] restock notify failed: {e}")
    if "categories" in data:
        store.save_category_order(data.get("categories") or [])
    # 상품에서 쓰는 카테고리는 순서 목록에 자동 추가
    cats = store.load_category_order()
    merged = list(cats)
    for p in out:
        c = str(p.get("category") or "").strip() or "기타"
        if c not in merged:
            merged.append(c)
    if merged != cats:
        store.save_category_order(merged)
    return jsonify({"ok": True, "products": out, "categories": merged})


@dash.route("/api/categories", methods=["POST"])
@_check
def api_categories_save():
    data = request.get_json(force=True, silent=True) or {}
    store.save_category_order(data.get("categories") or [])
    return jsonify({"ok": True, "categories": store.load_category_order()})


@dash.route("/api/products/defaults", methods=["POST"])
@_check
def api_products_defaults():
    data = request.get_json(force=True, silent=True) or {}
    mode = str(data.get("mode") or "merge")
    out = store.seed_default_products(merge=(mode != "replace"))
    cats = store.load_category_order()
    merged = list(cats)
    for p in out:
        c = str(p.get("category") or "").strip() or "기타"
        if c not in merged:
            merged.append(c)
    if merged != cats:
        store.save_category_order(merged)
    return jsonify({"ok": True, "products": out, "categories": merged})

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
    try:
        cur["delete_delay_sec"] = max(1, min(30, int(cur.get("delete_delay_sec", 5) or 5)))
    except Exception:
        cur["delete_delay_sec"] = 5
    try:
        cur["review_min_length"] = max(1, int(cur.get("review_min_length", 5) or 5))
    except Exception:
        cur["review_min_length"] = 5
    for k in ("mention_admin_on_create", "dm_on_open", "dm_on_close",
              "close_reason_required", "close_keep_channel", "delete_on_close",
              "one_ticket_per_user", "card_image_enabled", "stock_enabled"):
        v = cur.get(k, True)
        if isinstance(v, str):
            v = v.lower() == "true"
        cur[k] = bool(v)
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


def _load_reviews():
    import json as _j
    import os as _o
    rp = _o.path.join(store.DATA_DIR, "reviews.json")
    try:
        if _o.path.exists(rp):
            with open(rp, "r", encoding="utf-8") as f:
                return _j.load(f)
    except Exception:
        pass
    return []


@dash.route("/api/reviews", methods=["GET"])
@_check
def api_reviews():
    return jsonify({"ok": True, "reviews": _load_reviews()})


@dash.route("/api/commands", methods=["GET"])
@_check
def api_commands():
    return jsonify({"ok": True, "commands": store.load_commands()})


@dash.route("/api/commands", methods=["POST"])
@_check
def api_commands_save():
    import re as _re
    data = request.get_json(force=True, silent=True) or {}
    arr = data.get("commands", [])
    out = []
    seen = set()
    for c in arr[:25]:
        name = _re.sub(r"\s+", "", str(c.get("name", "") or "").strip())
        name = _re.sub(r"^/+", "", name)[:32]
        if not name or name in seen:
            continue
        seen.add(name)
        try:
            color = int(c.get("color", 0x5865F2))
        except Exception:
            color = 0x5865F2
        out.append({
            "name": name,
            "description": str(c.get("description", "") or "")[:100],
            "title": str(c.get("title", "") or "")[:256],
            "message": str(c.get("message", "") or "")[:4000],
            "color": color,
            "image_url": str(c.get("image_url", "") or "")[:500],
            "footer": str(c.get("footer", "") or "Apex Bot")[:2048],
            "ephemeral": bool(c.get("ephemeral", False)),
            "admin_only": bool(c.get("admin_only", False)),
            "enabled": bool(c.get("enabled", True)),
        })
    store.save_commands(out)
    return jsonify({"ok": True, "commands": out})

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


