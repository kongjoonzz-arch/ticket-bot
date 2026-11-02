# -*- coding: utf-8 -*-
"""구매 완료 / 후기 카드 (이미지 PNG 우선, 실패 시 V2·임베드 폴백)."""
import asyncio
import io
import os
import uuid

import discord
import store
import ticket_utils as tu
import ui_card_render as cards


def won(value):
    try:
        return f"{int(value):,}원"
    except Exception:
        return str(value)


def new_purchase_id():
    return uuid.uuid4().hex[:20]


def purchase_context(ticket, member=None):
    """영수증에 표시할 값들을 계산합니다."""
    t = ticket or {}
    p = t.get("product") or {}
    try:
        qty = int(p.get("quantity", 1) or 1)
    except Exception:
        qty = 1
    qty = max(1, qty)
    try:
        unit = int(p.get("price", 0) or 0)
    except Exception:
        unit = 0
    try:
        discount = int(p.get("discount", 0) or 0)
    except Exception:
        discount = 0
    discount = max(0, min(discount, unit * qty))
    total = unit * qty - discount
    buyer = ""
    if member is not None:
        buyer = str(getattr(member, "display_name", None) or getattr(member, "name", "") or "")
    buyer = buyer or str(t.get("user_name") or "구매자")
    return {
        "buyer": buyer,
        "category": str(p.get("category") or "").strip() or "기타",
        "product": str(p.get("name") or "상품"),
        "quantity": qty,
        "discount_txt": f"-{discount:,}원" if discount else "없음",
        "total_txt": won(total),
        "purchase_id": str(t.get("purchase_id") or ""),
        "at": tu.now_kst().strftime("%Y. %m. %d. %H:%M"),
    }


def _row(label, value):
    return f"{label} {'· ' * 8} **{value}**"


def _card_texts(settings, ctx):
    """(제목, 안내문, 구매자/항목/금액/하단) 문자열 묶음."""
    s = settings or {}
    title = str(s.get("purchase_card_title") or "구매 완료").strip()[:200]
    message = str(s.get("purchase_card_message") or s.get("complete_message")
                  or "구매가 정상적으로 완료되었습니다").strip()[:500]
    rows = "\n".join([
        _row("카테고리", ctx["category"]),
        _row("상품", ctx["product"]),
        _row("갯수", f"{ctx['quantity']}개"),
        _row("할인", ctx["discount_txt"]),
    ])
    foot = f"-# 구매 ID {ctx['purchase_id']} · {ctx['at']}"
    return title, message, rows, foot




def _color(settings):
    try:
        return int((settings or {}).get("panel_color", 0x5865F2))
    except Exception:
        return 0x5865F2


def build_receipt_v2(ctx, settings, delete_button=None):
    """Components V2 카드 payload. 실패하면 None."""
    try:
        title, message, rows, foot = _card_texts(settings, ctx)
        comps = [
            {"type": 10, "content": f"# ✅ {title}\n{message}".strip()},
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": f"**구매자**\n{ctx['buyer']}"},
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": rows},
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": f"**결제금액**\n# {ctx['total_txt']}"},
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": foot},
        ]
        if delete_button:
            comps.append({"type": 1, "components": [delete_button]})
        container = {"type": 17, "accent_color": _color(settings), "components": comps}
        return {"flags": 32768, "components": [container]}
    except Exception as e:
        print(f"[receipt] v2 build failed: {e}")
        return None


def build_receipt_embed(ctx, settings):
    title, message, _rows, _foot = _card_texts(settings, ctx)
    em = discord.Embed(title=f"✅ {title}", description=message, color=_color(settings))
    em.add_field(name="구매자", value=f"**{ctx['buyer']}**", inline=False)
    em.add_field(name="카테고리", value=ctx["category"], inline=True)
    em.add_field(name="상품", value=f"**{ctx['product']}**", inline=True)
    em.add_field(name="갯수", value=f"{ctx['quantity']}개", inline=True)
    em.add_field(name="할인", value=ctx["discount_txt"], inline=True)
    em.add_field(name="결제금액", value=f"**{ctx['total_txt']}**", inline=False)
    em.set_footer(text=f"구매 ID {ctx['purchase_id']} · {ctx['at']}")
    return em


async def _send_v2(channel, payload):
    tok = os.getenv("DISCORD_TOKEN", "")
    if not tok:
        return None
    import requests as _rq
    try:
        r = _rq.post(f"https://discord.com/api/v10/channels/{channel.id}/messages",
                     headers={"Authorization": f"Bot {tok}", "Content-Type": "application/json"},
                     json=payload, timeout=15)
        if r.status_code >= 300:
            print(f"[receipt] v2 send failed {r.status_code}: {r.text[:300]}")
            return None
        return r.json()
    except Exception as e:
        print(f"[receipt] v2 send error: {e}")
        return None


def card_brand(settings, guild=None):
    """카드 상단 브랜드명 (설정값 > 봇 이름=Apex Bot). '{server}' 는 서버 이름."""
    s = settings or {}
    brand = str(s.get("receipt_brand") or "").strip()
    if brand:
        if brand == "{server}" and guild is not None:
            try:
                nm = str(getattr(guild, "name", "") or "").strip()
                if nm:
                    return nm
            except Exception:
                pass
            return tu.BOT_NAME
        return brand
    return tu.BOT_NAME


def image_enabled(settings):
    v = (settings or {}).get("card_image_enabled", True)
    if isinstance(v, str):
        return v.strip().lower() == "true"
    return bool(v)


DEFAULT_ACCENT = "#3AD6A5"
REVIEW_ACCENT = "#F2C14E"


def _accent(settings, default):
    return str((settings or {}).get("card_accent") or "").strip() or default


def purchase_spec(ctx, settings, guild=None):
    title, message, _rows, _foot = _card_texts(settings, ctx)
    return {
        "brand": card_brand(settings, guild),
        "status": "결제 완료",
        "title": title or "구매 완료",
        "subtitle": message,
        "accent": _accent(settings, DEFAULT_ACCENT),
        "hero": {"label": "결제 금액",
                 "value": ctx["total_txt"],
                 "right_title": ctx["product"],
                 "right_sub": f"{ctx['category']} · {ctx['quantity']}개"},
        "rows": [("구매자", ctx["buyer"]),
                 ("카테고리", ctx["category"]),
                 ("상품", ctx["product"]),
                 ("갯수", f"{ctx['quantity']}개"),
                 ("할인", ctx["discount_txt"])],
        "footer_left": f"구매 ID {ctx['purchase_id']}",
        "footer_right": ctx["at"],
    }


def review_spec(ctx, settings, guild=None):
    stars = max(1, min(5, int(ctx.get("stars") or 5)))
    return {
        "brand": card_brand(settings, guild),
        "status": "후기 등록",
        "title": "고객 후기",
        "subtitle": f"{ctx.get('user') or ''} 님이 남긴 후기",
        "accent": _accent(settings, REVIEW_ACCENT),
        "hero": {"label": "별점", "value": f"{stars}.0", "stars": stars,
                 "right_title": ctx.get("product") or "상품",
                 "right_sub": ctx.get("category") or "기타"},
        "rows": [("작성자", str(ctx.get("user") or "")),
                 ("카테고리", ctx.get("category") or "기타"),
                 ("상품", ctx.get("product") or "상품"),
                 ("티켓", f"#{ctx.get('ticket_no')}")],
        "body": str(ctx.get("text") or ""),
        "footer_left": f"{tu.BOT_NAME} · 후기",
        "footer_right": ctx.get("at") or "",
    }


async def send_purchase_receipt(channel, ticket, member=None, view=None, delete_button=None):
    """구매 완료 카드 전송. (전송 결과, ctx) 반환."""
    s = store.load_settings()
    ctx = purchase_context(ticket, member)
    if image_enabled(s):
        png = await asyncio.to_thread(cards.render_card,
                                      purchase_spec(ctx, s, getattr(channel, "guild", None)))
        if png:
            try:
                f = discord.File(io.BytesIO(png), filename="purchase.png")
                em = discord.Embed()
                em.set_image(url="attachment://purchase.png")
                msg = await channel.send(embed=em, file=f, view=view)
                ctx["image"] = png
                return msg, ctx
            except Exception as e:
                print(f"[receipt] image send failed: {e}")
    payload = build_receipt_v2(ctx, s, delete_button=delete_button)
    if payload is not None:
        sent = await _send_v2(channel, payload)
        if sent is not None:
            return sent, ctx
    try:
        return await channel.send(embed=build_receipt_embed(ctx, s), view=view), ctx
    except Exception as e:
        print(f"[receipt] send failed: {e}")
        return None, ctx


# ---------------------------------------------------------------------------
# 후기 카드 (구매 완료 카드와 동일한 스타일)
# ---------------------------------------------------------------------------
REVIEW_COLOR = 0xFEE75C


async def send_v2(channel, payload):
    """다른 모듈에서 Components V2 메시지를 보낼 때 사용."""
    return await _send_v2(channel, payload)


def build_review_v2(ctx, settings):
    try:
        rows = "\n".join([
            _row("작성자", ctx["user"]),
            _row("카테고리", ctx["category"]),
            _row("상품", ctx["product"]),
            _row("별점", f"{ctx['star_txt']} ({ctx['stars']}/5)"),
            _row("티켓", f"#{ctx['ticket_no']}"),
        ])
        body = str(ctx.get("text") or "")[:3500] or "-"
        head = {"type": 9,
                "components": [{"type": 10, "content": f"# ⭐ 고객 후기\n{ctx['title']}"}]}
        avatar = str(ctx.get("avatar") or "")
        if avatar.startswith("http"):
            head["accessory"] = {"type": 11, "media": {"url": avatar}}
        comps = [
            head,
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": rows},
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": body},
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": f"-# {tu.BOT_NAME} · {ctx['at']} (KST)"},
        ]
        return {"flags": 32768,
                "components": [{"type": 17, "accent_color": REVIEW_COLOR, "components": comps}]}
    except Exception as e:
        print(f"[review] v2 build failed: {e}")
        return None


def build_review_embed(ctx, settings):
    em = discord.Embed(title=str(ctx.get("title") or "⭐ 고객 후기")[:256],
                       description=str(ctx.get("text") or "")[:4000],
                       color=REVIEW_COLOR)
    em.add_field(name="🛍️ 상품", value=f"**{ctx['product']}**\n🏷️ {ctx['category']}", inline=False)
    em.add_field(name="⭐ 별점", value=f"{ctx['star_txt']} ({ctx['stars']}/5)", inline=True)
    em.add_field(name="🎫 티켓", value=f"#{ctx['ticket_no']}", inline=True)
    em.set_footer(text=f"{tu.BOT_NAME} · {ctx['at']} (KST)")
    avatar = str(ctx.get("avatar") or "")
    if avatar.startswith("http"):
        try:
            em.set_thumbnail(url=avatar)
        except Exception:
            pass
    return em


async def send_review_card(guild, settings, ctx):
    """후기 채널에 카드 전송 (이미지 → V2 → 임베드). 보낸 메시지 or None."""
    s = settings or store.load_settings()
    rid = str(s.get("review_channel_id") or "").strip()
    if not rid.isdigit():
        return None
    ch = guild.get_channel(int(rid))
    if ch is None:
        return None
    if image_enabled(s):
        png = await asyncio.to_thread(cards.render_card, review_spec(ctx, s, guild))
        if png:
            try:
                f = discord.File(io.BytesIO(png), filename="review.png")
                em = discord.Embed()
                em.set_image(url="attachment://review.png")
                return await ch.send(embed=em, file=f)
            except Exception as e:
                print(f"[review] image send failed: {e}")
    payload = build_review_v2(ctx, s)
    if payload is not None:
        sent = await _send_v2(ch, payload)
        if sent is not None:
            return sent
    try:
        return await ch.send(embed=build_review_embed(ctx, s))
    except Exception as e:
        print(f"[review] send failed: {e}")
        return None


async def send_log_with_card(guild, settings, png, embed):
    """구매로그 채널에 카드 이미지 + 요약 임베드를 함께 전송."""
    s = settings or store.load_settings()
    cid = str(s.get("purchase_log_channel_id") or "").strip()
    if not cid.isdigit():
        return False
    ch = guild.get_channel(int(cid))
    if ch is None:
        return False
    try:
        if png:
            f = discord.File(io.BytesIO(png), filename="purchase-log.png")
            embed.set_image(url="attachment://purchase-log.png")
            await ch.send(embed=embed, file=f)
        else:
            await ch.send(embed=embed)
        return True
    except Exception as e:
        print(f"[log] purchase log card failed: {e}")
        try:
            await ch.send(embed=embed)
            return True
        except Exception as e2:
            print(f"[log] purchase log failed: {e2}")
            return False
