# -*- coding: utf-8 -*-
"""티켓 생성/권한/요약 관련 헬퍼."""
import re
import discord
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


def now_kst_str():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M")


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


def build_summary_embed(kind: str, user: discord.abc.User, product, answers: list, ticket_no: int) -> discord.Embed:
    kind_label = "🛒 구매문의" if kind == "buy" else "❓ 오류문의"
    color = 0x57F287 if kind == "buy" else 0xFEE75C
    embed = discord.Embed(title=f"{kind_label} — 티켓 #{ticket_no}", color=color)
    embed.add_field(name="문의자", value=f"{user.mention} (`{user.id}`)", inline=False)
    if kind == "buy" and product:
        price = product.get("price", 0)
        try:
            price_txt = f"{int(price):,}원"
        except Exception:
            price_txt = str(price)
        embed.add_field(
            name="선택 상품",
            value=f"**{product.get('name', '(삭제된 상품)')}** — {price_txt} (재고 {product.get('stock', '?')})",
            inline=False,
        )
    lines = []
    for a in answers:
        label = a.get("label", "질문")
        value = (a.get("value") or "미입력").strip() or "미입력"
        if len(value) > 500:
            value = value[:500] + "…"
        lines.append(f"**Q. {label}**\n> {value}")
    embed.add_field(name="📝 답변 정리", value="\n\n".join(lines) if lines else "답변 없음", inline=False)
    embed.set_footer(text=f"접수 시각 {now_kst_str()} (KST)")
    return embed


async def create_ticket_channel(guild: discord.Guild, user: discord.Member, kind: str,
                                ticket_no: int, settings: dict):
    """관리자+본인만 볼 수 있는 비공개 채널 생성."""
    kind_ko = "구매문의" if kind == "buy" else "오류문의"
    name = safe_channel_name(f"{kind_ko}-{ticket_no}-{user.display_name}")
    category = None
    cat_id = str(settings.get("ticket_category_id") or "").strip()
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
                                              read_message_history=True),
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
        topic=f"티켓 #{ticket_no} | {kind_ko} | {user.id}",
        reason=f"티켓 #{ticket_no} 생성 ({user})",
    )
    return channel


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


async def send_dm(user, title, message):
    try:
        em = discord.Embed(title=(title or "알림")[:256], description=(message or "")[:4000], color=0x5865F2)
        await user.send(embed=em)
        return True
    except discord.Forbidden:
        print(f"[dm] DM 차단됨: {user}")
        return False
    except Exception as e:
        print(f"[dm] DM 실패: {e}")
        return False

