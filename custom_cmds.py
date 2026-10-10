# -*- coding: utf-8 -*-
"""Dashboard custom commands -> discord slash commands."""
import re
import discord
from discord import app_commands
import store
import ticket_utils as tu


def _norm_name(name):
    t = re.sub(r"\s+", "", str(name or "").strip())
    t = re.sub(r"^/+", "", t)
    return t[:32]


async def _run_custom(interaction, cmd):
    s = store.load_settings()
    only_admin = bool(cmd.get("admin_only", False))
    if only_admin and not tu.is_admin(interaction.user, s):
        await interaction.response.send_message(embed=tu.err_embed("관리자만 사용할 수 있어요."), ephemeral=True)
        return
    try:
        color = int(cmd.get("color", 0x5865F2))
    except Exception:
        color = 0x5865F2
    mapping = {"user_mention": interaction.user.mention,
               "user": str(interaction.user),
               "channel": interaction.channel.mention if interaction.channel else ""}
    title = tu.fill(cmd.get("title", ""), mapping)[:256]
    msg = tu.fill(cmd.get("message", ""), mapping)[:4000]
    em = discord.Embed(title=title or cmd.get("name", tu.BOT_NAME), description=msg or "━━━━━━━━━━━━━━━", color=color)
    img = str(cmd.get("image_url", "") or "").strip()
    if img.startswith("http"):
        em.set_image(url=img)
    foot = str(cmd.get("footer", "") or tu.BOT_NAME).strip()
    em.set_footer(text=(foot[:2048] if foot else tu.BOT_NAME))
    em.timestamp = tu.now_kst()
    eph = bool(cmd.get("ephemeral", False))
    try:
        await interaction.response.send_message(embed=em, ephemeral=eph)
    except Exception as e:
        print(f"[custom] send failed: {e}")


def sync_custom_commands(tree, guild_obj=None):
    """기존 커스텀 명령 제거 후 대시보드 목록으로 재등록. 등록된 이름 목록 반환."""
    for c in list(tree.get_commands()):
        if getattr(c, "_apex_custom", False):
            tree.remove_command(c.name, guild=guild_obj)
    names = []
    for cmd in store.load_commands():
        if not cmd.get("enabled", True):
            continue
        name = _norm_name(cmd.get("name", ""))
        if not name or len(name) < 1:
            continue
        desc = str(cmd.get("description", "") or "Apex Bot 안내")[:100]

        def _make(c):
            async def _cb(interaction):
                await _run_custom(interaction, c)
            return _cb

        sc = app_commands.Command(name=name, description=desc,
                                  callback=_make(dict(cmd)), nsfw=False)
        sc._apex_custom = True
        try:
            if guild_obj is not None:
                tree.add_command(sc, guild=guild_obj)
            else:
                tree.add_command(sc)
            names.append(name)
        except Exception as e:
            print(f"[custom] register failed {name}: {e}")
    return names
