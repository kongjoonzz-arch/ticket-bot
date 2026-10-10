# -*- coding: utf-8 -*-
"""Close reason modal + shared close logic."""
import discord
import store
import ticket_utils as tu


async def do_close_ticket(guild, channel, admin_user, reason):
    import asyncio
    s = store.load_settings()
    reason = (reason or "").strip() or "사유 미입력"
    tickets = store.load_tickets()
    target = None
    for t in tickets:
        if t.get("channel_id") == channel.id:
            t["status"] = "closed"
            t["closed_at"] = tu.now_kst_str()
            t["close_reason"] = reason
            t["closed_by"] = str(admin_user)
            target = t
    store.save_tickets(tickets)
    kind = target.get("kind", "?") if target else "?"
    no = target.get("no", "?") if target else "?"
    user_id = target.get("user_id") if target else None
    kind_ko = "구매 문의" if kind == "buy" else "오류 문의" if kind == "error" else str(kind)
    try:
        delay = int(s.get("delete_delay_sec", 5) or 5)
    except Exception:
        delay = 5
    em = discord.Embed(title=f"🔒 티켓 #{no} 닫힘", color=0xED4245)
    em.description = (
        "━━━━━━━━━━━━━━━\n"
        f"{s.get('close_message', '이용해 주셔서 감사합니다!')}\n"
        "━━━━━━━━━━━━━━━"
    )
    em.add_field(name="📌 닫기 사유", value=f"> {reason}", inline=False)
    em.add_field(name="👤 담당", value=admin_user.mention, inline=True)
    em.add_field(name="🗑️ 채널 삭제", value=f"{delay}초 후 자동 삭제", inline=True)
    em.set_footer(text=f"Ticket #{no} · {tu.now_kst_str()} (KST)")
    em.timestamp = tu.now_kst()
    try:
        await channel.send(embed=em)
    except Exception:
        pass
    log = discord.Embed(title=f"🔒 Ticket #{no} closed", color=0xED4245)
    log.description = "━━━━━━━━━━━━━━━"
    log.add_field(name="티켓", value=f"{channel.mention} · {kind_ko}", inline=False)
    log.add_field(name="담당", value=admin_user.mention, inline=True)
    log.add_field(name="사유", value=reason[:1000], inline=False)
    log.set_footer(text=f"{tu.now_kst_str()} (KST)")
    log.timestamp = tu.now_kst()
    await tu.send_log(guild, s, log)
    if user_id and s.get("dm_on_close"):
        member = None
        try:
            member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
        except Exception:
            member = None
        if member is not None:
            mapping = {"no": no, "kind": kind_ko, "user_mention": member.mention, "reason": reason}
            title = tu.fill(s.get("dm_close_title", ""), mapping).replace("#{no}", f"#{no}")
            msg = tu.fill(s.get("dm_close_message", ""), mapping).replace("#{no}", f"#{no}")
            thumb = None
            try:
                thumb = guild.icon.url if getattr(guild, "icon", None) else None
            except Exception:
                thumb = None
            await tu.send_dm(member, title, msg, color=0xED4245, thumb_url=thumb, footer=f"Ticket #{no} · Closed")
    if bool(s.get("delete_on_close", True)):
        await asyncio.sleep(max(1, min(delay, 30)))
        try:
            await channel.delete(reason=f"ticket #{no} closed: {reason[:100]}")
        except Exception as e:
            print(f"[ticket] delete failed: {e}")


class CloseReasonModal(discord.ui.Modal):
    def __init__(self):
        s = store.load_settings()
        required = bool(s.get("close_reason_required", False))
        ph = str(s.get("close_reason_placeholder", "") or "")[:100] or None
        super().__init__(title="Ticket Close")
        self.add_item(discord.ui.TextInput(label="Close reason", placeholder=ph,
                                           required=required, max_length=300,
                                           style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)
        reason = (self.children[0].value or "").strip()
        await do_close_ticket(interaction.guild, interaction.channel, interaction.user, reason)
        try:
            em = discord.Embed(title="🔒 티켓 닫기 완료", color=0xED4245)
            em.description = f"사유: {reason or '사유 미입력'}\n채널이 곧 삭제됩니다."
            await interaction.followup.send(embed=em, ephemeral=True)
        except Exception:
            pass
