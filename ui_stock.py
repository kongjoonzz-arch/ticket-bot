# -*- coding: utf-8 -*-
"""재고 입고 알림 (입고 채널로 전송).

- 대시보드에서 재고를 늘리거나 `/재고추가` 명령을 쓰면 입고 채널에 알림이 갑니다.
- 입고 채널 ID(`stock_log_channel_id`)가 비어 있으면 구매로그 → 티켓로그 순서로 대체합니다.
"""
import store
import ticket_utils as tu

CHANNEL_KEYS = ("stock_log_channel_id", "purchase_log_channel_id", "ticket_log_channel_id")


def restock_channel_id(settings=None):
    s = settings or store.load_settings()
    for k in CHANNEL_KEYS:
        v = str(s.get(k) or "").strip()
        if v.isdigit():
            return v
    return ""


def _num(v):
    try:
        return int(v)
    except Exception:
        return None


def build_restock_embed(settings, items, source=""):
    s = settings or store.load_settings()
    lines = []
    for it in items or []:
        name = str(it.get("name") or "상품")
        cat = str(it.get("category") or "").strip() or "기타"
        added = _num(it.get("added")) or 0
        stock = _num(it.get("stock"))
        tail = f" → 현재 **{stock}개**" if stock is not None and stock >= 0 else " → 현재 무제한"
        lines.append(f"**{name}** `+{added}개`{tail}\n> 🏷️ {cat}")
    desc = "📦 **재고가 입고되었습니다**\n\n" + "\n\n".join(lines[:15])
    if len(lines) > 15:
        desc += f"\n\n…외 {len(lines) - 15}건"
    em = tu.apex_embed(s, "📦 재고 입고 알림", desc, color=0x57F287)
    if source:
        em.add_field(name="처리", value=str(source)[:250], inline=True)
    em.add_field(name="시각", value=f"{tu.now_kst_str()} (KST)", inline=True)
    em.add_field(name="안내", value="이 알림은 재고가 늘어날 때 자동으로 전송됩니다.", inline=False)
    return em


def send_restock(settings=None, items=None, source="", content=None):
    """입고 알림 전송. 성공 여부 반환."""
    s = settings or store.load_settings()
    cid = restock_channel_id(s)
    if not cid or not items:
        return False
    return tu.send_rest_embed(cid, build_restock_embed(s, items, source), content=content)
