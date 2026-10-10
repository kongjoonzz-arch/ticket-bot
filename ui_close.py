# -*- coding: utf-8 -*-
"""Close reason modal + shared close logic."""
import discord
import store
import ticket_utils as tu


async def do_close_ticket(guild, channel, admin_user, reason):
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
    await channel.send(s.get("close_message", "Ticket closed."))
    try:
        await channel.send(f"📌 닫기 사유: {reason}\n담당: {admin_user.mention}")
    except Exception:
        pass
    kind = target.get("kind", "?") if target else "?"
    no = target.get("no", "?") if target else "?"
    user_id = target.get("user_id") if target else None
    log = discord.Embed(title=f"Ticket #{no} closed",
                        description=f"{channel.mention} by {admin_user.mention}\n사유: {reason}",
                        color=0xED4245)
    await tu.send_log(guild, s, log)
    if user_id and s.get("dm_on_close"):
        member = None
        try:
            member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
        except Exception:
            member = None
        if member is not None:
            kind_ko = "구매문의" if kind == "buy" else "오류문의"
            mapping = {"no": no, "kind": kind_ko, "user_mention": member.mention, "reason": reason}
            title = tu.fill(s.get("dm_close_title", ""), mapping).replace("#{no}", f"#{no}")
            msg = tu.fill(s.get("dm_close_message", ""), mapping).replace("#{no}", f"#{no}")
            await tu.send_dm(member, title, msg)
    overw = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }
    try:
        await channel.edit(overwrites=overw, reason=f"ticket close: {reason}")
    except Exception as e:
        print(f"[ticket] lock failed: {e}")


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
        await interaction.response.defer(thinking=False)
        reason = self.children[0].value or ""
        await do_close_ticket(interaction.guild, interaction.channel, interaction.user, reason)
        try:
            await interaction.followup.send(f"Ticket closed. 사유: {reason or '사유 미입력'}", ephemeral=True)
        except Exception:
            pass
