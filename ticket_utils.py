# -*- coding: utf-8 -*-
"""티켓 생성/권한/요약 관련 헬퍼."""
import re
import discord
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
BOT_NAME = "Apex Bot"
BOT_COLOR = 0x5865F2
DIV = "━━━━━━━━━━━━━━━"


def bot_footer(settings=None):
    return BOT_NAME


def parse_emoji(text):
    """서버 커스텀 이모지(<:name:id> / <a:name:id>) 또는 유니코드 이모지 파싱."""
    t = str(text or "").strip()
    if not t:
        return None
    import re as _re
    m = _re.fullmatch(r"<(a)?:([A-Za-z0-9_~]+):(\d+)>", t)
    if m:
        animated = bool(m.group(1))
        return discord.PartialEmoji(name=m.group(2), id=int(m.group(3)), animated=animated)
    if len(t) <= 8:
        return t
    return None


def apex_embed(settings, title, desc="", color=None):
    try:
        cc = int(color) if color is not None else int((settings or {}).get("panel_color", BOT_COLOR))
    except Exception:
        cc = BOT_COLOR
    em = discord.Embed(title=str(title or BOT_NAME)[:256],
                       description=(str(desc or "")[:4000] or DIV),
                       color=cc)
    em.set_footer(text=BOT_NAME)
    em.timestamp = datetime.now(KST)
    return em


def now_kst_str():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M")


def now_kst():
    return datetime.now(KST)


def err_embed(text):
    em = discord.Embed(title=f"{BOT_NAME} · 안내", description=str(text or "")[:4000], color=0xED4245)
    em.set_footer(text=BOT_NAME)
    em.timestamp = datetime.now(KST)
    return em


def ok_embed(title, text, color=0x57F287):
    try:
        cc = int(color)
    except Exception:
        cc = 0x57F287
    em = discord.Embed(title=str(title or BOT_NAME)[:256], description=str(text or "")[:4000], color=cc)
    em.set_footer(text=BOT_NAME)
    em.timestamp = datetime.now(KST)
    return em


def is_admin(member: discord.Member, settings: dict) -> bool:
    try:
        if getattr(member, "guild_permissions", None) and member.guild_permissions.administrator:
            return True
        if getattr(member, "guild_permissions", None) and member.guild_permissions.manage_channels:
            return True
    except Exception:
        pass
    role_id = str(settings.get("admin_role_id") or "").strip()
    if role_id.isdigit():
        try:
            return any(r.id == int(role_id) for r in getattr(member, "roles", []))
        except Exception:
            return False
    return False


def safe_channel_name(text: str, max_len: int = 90) -> str:
    t = re.sub(r"[^\w가-힣\- ]+", "", text or "").strip().replace(" ", "-")
    t = re.sub(r"-{2,}", "-", t)
    return (t or "ticket")[:max_len]


def admin_mention_text(settings: dict, guild: discord.Guild) -> str:
    role_id = str(settings.get("admin_role_id") or "").strip()
    if role_id.isdigit() and guild is not None:
        role = guild.get_role(int(role_id))
        if role is not None:
            return role.mention
    return "@관리자"


def build_summary_embed(kind: str, user: discord.abc.User, product, answers: list, ticket_no: int = 0) -> discord.Embed:
    is_buy = (kind == "buy")
    kind_label = "🛒 구매 문의" if is_buy else "❓ 오류 문의"
    color = 0x5865F2 if is_buy else 0xEB459E
    embed = discord.Embed(title=kind_label, color=color)
    embed.description = "━━━━━━━━━━━━━━━\n접수가 완료되었습니다. 관리자가 확인 중입니다.\n━━━━━━━━━━━━━━━"
    embed.add_field(name="👤 문의자", value=f"{user.mention}", inline=True)
    embed.add_field(name="🕒 접수 시각", value=f"{now_kst_str()} (KST)", inline=True)
    if is_buy and product:
        price = product.get("price", 0)
        try:
            price_txt = f"{int(price):,}원"
        except Exception:
            price_txt = str(price)
        stock = product.get("stock", "?")
        category = str(product.get("category") or "").strip() or "기타"
        desc = str(product.get("description", "") or "").strip()
        val = f"🏷️ {category}\n**{product.get('name', '(삭제된 상품)')}**\n💰 {price_txt} · 📦 재고 {stock}"
        if desc:
            val += f"\n> {desc[:300]}"
        embed.add_field(name="🎁 선택 상품", value=val, inline=False)
    lines = []
    for i, a in enumerate(answers, 1):
        label = a.get("label", "질문")
        value = (a.get("value") or "미입력").strip() or "미입력"
        if len(value) > 500:
            value = value[:500] + "…"
        lines.append(f"**{i}. {label}**\n> {value}")
    embed.add_field(name="📝 답변 정리", value="\n\n".join(lines) if lines else "답변 없음", inline=False)
    embed.set_footer(text="추가 설명은 이 채널에 입력해주세요")
    embed.timestamp = datetime.now(KST)
    try:
        avatar = getattr(user, "display_avatar", None)
        if avatar is not None:
            embed.set_thumbnail(url=avatar.url)
    except Exception:
        pass
    return embed


async def create_ticket_channel(guild: discord.Guild, user: discord.Member, kind: str,
                                ticket_no: int, settings: dict):
    """관리자+본인만 볼 수 있는 비공개 채널 생성 (채널 이름은 닉네임만)."""
    kind_ko = "구매 문의" if kind == "buy" else "오류 문의"
    nick = str(getattr(user, "display_name", None) or getattr(user, "name", "") or "ticket")
    name = safe_channel_name(nick) or "ticket"
    key = "buy_category_id" if kind == "buy" else "error_category_id"
    cat_id = str(settings.get(key) or settings.get("ticket_category_id") or "").strip()
    category = None
    if cat_id.isdigit():
        category = guild.get_channel(int(cat_id))
        if category is not None and not isinstance(category, discord.CategoryChannel):
            category = None

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                          read_message_history=True, attach_files=True,
                                          embed_links=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                              manage_channels=True, manage_messages=True,
                                              read_message_history=True,
                                              attach_files=True, embed_links=True),
    }
    role_id = str(settings.get("admin_role_id") or "").strip()
    if role_id.isdigit():
        role = guild.get_role(int(role_id))
        if role is not None:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                manage_channels=True, manage_messages=True)

    channel = await guild.create_text_channel(
        name=name, category=category, overwrites=overwrites,
        topic=f"{kind_ko} | {user.id}",
        reason=f"티켓 생성 ({user})",
    )
    return channel


def send_rest_embed(channel_id, embed, content=None):
    """봇 이벤트 루프 밖(대시보드/스레드)에서도 채널에 임베드를 보낼 수 있게 REST 사용."""
    import os as _os
    cid = str(channel_id or "").strip()
    tok = _os.getenv("DISCORD_TOKEN", "")
    if not cid.isdigit() or not tok:
        return False
    try:
        import requests as _rq
        body = {"embeds": [embed.to_dict()]}
        if content:
            body["content"] = str(content)[:2000]
        r = _rq.post(f"https://discord.com/api/v10/channels/{cid}/messages",
                     headers={"Authorization": f"Bot {tok}",
                              "Content-Type": "application/json"},
                     json=body, timeout=15)
        if r.status_code >= 300:
            print(f"[rest] send failed {r.status_code}: {r.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"[rest] send error: {e}")
        return False


async def send_log(guild: discord.Guild, settings: dict, embed: discord.Embed):
    log_id = str(settings.get("ticket_log_channel_id") or "").strip()
    if not log_id.isdigit():
        return
    ch = guild.get_channel(int(log_id))
    if ch is None:
        return
    try:
        await ch.send(embed=embed)
    except Exception as e:
        print(f"[log] 로그 전송 실패: {e}")


def fill(text, mapping):
    out = str(text or "")
    for k, v in (mapping or {}).items():
        out = out.replace("{" + k + "}", str(v))
    return out


def build_announce(settings, override=None):
    cfg = dict(settings or {})
    if override:
        cfg.update({k: v for k, v in override.items() if v is not None})
    try:
        color = int(cfg.get("announce_color", 0x5865F2))
    except Exception:
        color = 0x5865F2
    em = discord.Embed(
        title=str(cfg.get("announce_title", "공지") or "공지")[:256],
        description=str(cfg.get("announce_message", "") or "")[:4000],
        color=color,
    )
    foot = str(cfg.get("announce_footer", "") or "").strip()
    if foot:
        em.set_footer(text=foot[:2048])
    img = str(cfg.get("announce_image_url", "") or "").strip()
    if img.startswith("http"):
        em.set_image(url=img)
    em.timestamp = datetime.now(KST)
    return em


def announce_mention_text(settings, guild, override=None):
    cfg = dict(settings or {})
    if override:
        cfg.update({k: v for k, v in override.items() if v is not None})
    mode = str(cfg.get("announce_mention", "none") or "none")
    if mode == "everyone":
        return "@everyone"
    if mode == "here":
        return "@here"
    if mode == "role":
        rid = str(cfg.get("announce_mention_role_id", "") or "").strip()
        if rid.isdigit() and guild is not None:
            role = guild.get_role(int(rid))
            if role is not None:
                return role.mention
        return ""
    return ""


async def send_dm(user, title, message, color=0x5865F2, thumb_url=None, footer=None):
    try:
        cc = int(color)
    except Exception:
        cc = 0x5865F2
    try:
        em = discord.Embed(title=str(title or BOT_NAME)[:256],
                           description="━━━━━━━━━━━━━━━\n" + str(message or "")[:3800] + "\n━━━━━━━━━━━━━━━",
                           color=cc)
        em.set_footer(text=str(footer or BOT_NAME)[:2048])
        em.timestamp = datetime.now(KST)
        if thumb_url:
            em.set_thumbnail(url=thumb_url)
        await user.send(embed=em)
        return True
    except discord.Forbidden:
        print(f"[dm] DM 차단됨: {user}")
        return False
    except Exception as e:
        print(f"[dm] DM 실패: {e}")
        return False


async def send_purchase_log(guild, settings, embed):
    pid = str(settings.get("purchase_log_channel_id") or "").strip()
    if not pid.isdigit():
        return
    ch = guild.get_channel(int(pid))
    if ch is None:
        return
    try:
        await ch.send(embed=embed)
    except Exception as e:
        print(f"[purchase-log] 실패: {e}")


async def send_review(guild, settings, embed):
    rid = str(settings.get("review_channel_id") or "").strip()
    if not rid.isdigit():
        return None
    ch = guild.get_channel(int(rid))
    if ch is None:
        return None
    try:
        return await ch.send(embed=embed)
    except Exception as e:
        print(f"[review] 실패: {e}")
        return None


def find_open_ticket_by_user(user_id):
    for t in load_tickets_safe():
        if str(t.get("user_id")) == str(user_id) and t.get("status") == "open":
            return t
    return None


def load_tickets_safe():
    try:
        import store as _store
        return _store.load_tickets()
    except Exception:
        return []

