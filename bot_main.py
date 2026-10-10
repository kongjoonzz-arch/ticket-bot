import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import store
import ticket_utils as tu
import v2panel

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = os.getenv("GUILD_ID", "0")
try:
    GUILD_ID_INT = int(GUILD_ID)
except Exception:
    GUILD_ID_INT = 0

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.dm_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DIV = "━━━━━━━━━━━━━━━"


async def _v2_send(channel, payload):
    tok = os.getenv("DISCORD_TOKEN", "")
    if not tok:
        return None
    import requests as _rq
    try:
        r = _rq.post(f"https://discord.com/api/v10/channels/{channel.id}/messages",
                     headers={"Authorization": f"Bot {tok}", "Content-Type": "application/json"},
                     json=payload, timeout=15)
        if r.status_code >= 300:
            print(f"[v2] send failed {r.status_code}: {r.text[:300]}")
            return None
        return r.json()
    except Exception as e:
        print(f"[v2] send error: {e}")
        return None


async def send_panel_message(channel, view=None):
    """V2 Container 지원하면 임베드 안에 버튼, 아니면 기존 임베드+버튼."""
    s = store.load_settings()
    payload = v2panel.build_panel_v2(s)
    if payload is not None:
        sent = await _v2_send(channel, payload)
        if sent is not None:
            return ("v2", None)
    em = await build_panel_embed()
    if view is None:
        from ui_panel import make_panel_view
        view = make_panel_view(s)
    msg = await channel.send(embed=em, view=view)
    return ("legacy", msg)


async def build_panel_embed():
    s = store.load_settings()
    try:
        color = int(s.get("panel_color", 0x5865F2))
    except Exception:
        color = 0x5865F2
    title = str(s.get("panel_title", "") or "🎫 PREMIUM TICKET")
    desc = str(s.get("panel_description", "") or "")[:4000]
    em = discord.Embed(title=title[:256], color=color)
    lines = []
    if desc.strip():
        lines.append(desc.strip())
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━")
    buy_label = str(s.get("panel_button_buy", "") or "구매 문의").strip()
    err_label = str(s.get("panel_button_error", "") or "오류 문의").strip()
    buy_e = str(s.get("panel_button_buy_emoji", "") or "").strip()
    err_e = str(s.get("panel_button_error_emoji", "") or "").strip()
    buy_head = f"{buy_e} **{buy_label}**" if buy_e else f"**{buy_label}**"
    err_head = f"{err_e} **{err_label}**" if err_e else f"**{err_label}**"
    lines.append(f"🔹 {buy_head}\n상품 구매·입금 안내는 아래 **첫 번째 버튼**을 눌러주세요.")
    lines.append("")
    lines.append(f"🔸 {err_head}\n입금 오류·상품 문제는 아래 **두 번째 버튼**을 눌러주세요.")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("⏱️ 24시간 운영 · DM 차단 시 알림이 안 가니 미리 해제해주세요.")
    em.description = "\n".join(lines)[:4000]
    foot = str(s.get("panel_footer", "") or "").strip()
    em.set_footer(text=(foot[:2048] if foot else "24시간 운영 · 평균 응답 10분 이내"))
    img = str(s.get("panel_image_url", "") or "").strip()
    if img.startswith("http"):
        em.set_image(url=img)
    thumb = str(s.get("panel_thumbnail_url", "") or "").strip()
    if thumb.startswith("http"):
        em.set_thumbnail(url=thumb)
    em.timestamp = tu.now_kst()
    return em


