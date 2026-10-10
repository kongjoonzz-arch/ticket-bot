# -*- coding: utf-8 -*-
"""Components V2 panel: Container 안에 텍스트 + 버튼을 함께 배치."""
import re


def _emoji_obj(text):
    t = str(text or "").strip()
    if not t:
        return None
    m = re.fullmatch(r"<(a)?:([A-Za-z0-9_~]+):(\d+)>", t)
    if m:
        return {"id": m.group(3), "name": m.group(2), "animated": bool(m.group(1))}
    if len(t) <= 8:
        return {"name": t}
    return None


def _color_hex(value, default=0x5865F2):
    try:
        return int(value)
    except Exception:
        return default


def build_panel_v2(s):
    """성공시 REST payload dict, 실패시 None."""
    try:
        color = _color_hex((s or {}).get("panel_color", 0x5865F2))
        title = str((s or {}).get("panel_title", "") or "Apex Bot")[:256]
        desc = str((s or {}).get("panel_description", "") or "")[:3000]
        buy_label = str((s or {}).get("panel_button_buy", "") or "구매 문의").strip()[:80]
        err_label = str((s or {}).get("panel_button_error", "") or "오류 문의").strip()[:80]
        buy_e = _emoji_obj((s or {}).get("panel_button_buy_emoji", ""))
        err_e = _emoji_obj((s or {}).get("panel_button_error_emoji", ""))
        foot = str((s or {}).get("panel_footer", "") or "Apex Bot").strip()[:2048]
        img = str((s or {}).get("panel_image_url", "") or "").strip()
        thumb = str((s or {}).get("panel_thumbnail_url", "") or "").strip()
        hex_color = f"#{color:06x}"
        body = []
        if desc.strip():
            body.append(desc.strip())
            body.append("")
        body.append(f"**{buy_label}** — 상품 구매·입금 안내")
        body.append(f"**{err_label}** — 입금 오류·상품 문제")
        body.append("")
        body.append("아래 버튼을 눌러주세요.")
        text = f"# {title}\n" + "\n".join(body)
        buy_btn = {"type": 2, "style": 1, "label": buy_label, "custom_id": "panel:buy"}
        if buy_e:
            buy_btn["emoji"] = buy_e
        err_btn = {"type": 2, "style": 2, "label": err_label, "custom_id": "panel:error"}
        if err_e:
            err_btn["emoji"] = err_e
        section = {"type": 9, "components": [{"type": 10, "content": text[:4000]}],
                   "accessory": buy_btn}
        row = {"type": 1, "components": [err_btn]}
        container = {"type": 17, "accent_color": color, "components": [section, row]}
        comps = [container]
        if thumb.startswith("http") or img.startswith("http"):
            gallery = {"type": 12, "items": []}
            if thumb.startswith("http"):
                gallery["items"].append({"media": {"url": thumb}})
            if img.startswith("http"):
                gallery["items"].append({"media": {"url": img}})
            comps.append(gallery)
        payload = {"flags": 32768, "components": comps}
        if foot:
            payload["components"].append({"type": 10, "content": f"-# {foot}"})
        _ = hex_color
        return payload
    except Exception as e:
        print(f"[v2] build failed: {e}")
        return None
