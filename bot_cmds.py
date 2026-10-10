import discord
from discord import app_commands
import store
import ticket_utils as tu
from ui_panel import PanelView
from ui_control import TicketControlView
from bot_main import bot, build_panel_embed, GUILD_ID_INT

@bot.event
async def on_ready():
    print(f"[bot] logged in as {bot.user}")
    s = store.load_settings()
    bot.add_view(PanelView(s.get("panel_button_buy", "Buy"), s.get("panel_button_error", "Error")))
    bot.add_view(TicketControlView())
    try:
        if GUILD_ID_INT:
            g = discord.Object(id=GUILD_ID_INT)
            bot.tree.copy_global_to(guild=g)
            synced = await bot.tree.sync(guild=g)
            print(f"[bot] synced {len(synced)} cmds to guild {GUILD_ID_INT}")
        else:
            synced = await bot.tree.sync()
            print(f"[bot] synced {len(synced)} global cmds")
    except Exception as e:
        print(f"[bot] sync failed: {e}")

def _is_admin_interaction(interaction):
    s = store.load_settings()
    return tu.is_admin(interaction.user, s)

@bot.tree.command(name="panel", description="Send ticket panel to this channel (admin)")
async def panel_cmd(interaction: discord.Interaction):
    if not _is_admin_interaction(interaction):
        await interaction.response.send_message("Admin only.", ephemeral=True)
        return
    em = await build_panel_embed()
    await interaction.response.send_message("Panel sent.", ephemeral=True)
    s2 = store.load_settings()
    await interaction.channel.send(embed=em, view=PanelView(s2.get("panel_button_buy", "Buy"), s2.get("panel_button_error", "Error")))

@bot.tree.command(name="ticket-close", description="Close this ticket (admin)")
@app_commands.describe(reason="Close reason (sent to channel, log and user DM)")
async def close_cmd(interaction: discord.Interaction, reason: str = ""):
    s = store.load_settings()
    if not tu.is_admin(interaction.user, s):
        await interaction.response.send_message("Admin only.", ephemeral=True)
        return
    if not reason and bool(s.get("close_reason_required", False)):
        from ui_close import CloseReasonModal
        await interaction.response.send_modal(CloseReasonModal())
        return
    await interaction.response.defer(thinking=False)
    from ui_close import do_close_ticket
    await do_close_ticket(interaction.guild, interaction.channel, interaction.user, reason)
    try:
        await interaction.followup.send(f"Ticket closed. 사유: {reason or '사유 미입력'}", ephemeral=True)
    except Exception:
        pass

@bot.tree.command(name="ticket-confirm", description="Confirm purchase (admin)")
async def confirm_cmd(interaction: discord.Interaction):
    if not _is_admin_interaction(interaction):
        await interaction.response.send_message("Admin only.", ephemeral=True)
        return
    await interaction.response.send_message("Purchase confirmed by admin.")


@bot.tree.command(name="announce", description="Send embed notice (admin)")
@app_commands.describe(channel="Notice channel (empty = dashboard setting)",
                       title="Notice title (empty = dashboard setting)",
                       message="Notice message (empty = dashboard setting)",
                       mention="Mention setting")
@app_commands.choices(mention=[
    app_commands.Choice(name="none", value="none"),
    app_commands.Choice(name="everyone", value="everyone"),
    app_commands.Choice(name="here", value="here"),
    app_commands.Choice(name="role", value="role"),
])
async def announce_cmd(interaction: discord.Interaction, channel: discord.TextChannel = None,
                       title: str = "", message: str = "",
                       mention: app_commands.Choice[str] = None):
    s = store.load_settings()
    if not tu.is_admin(interaction.user, s):
        await interaction.response.send_message("Admin only.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    target = channel
    if target is None:
        cid = str(s.get("announce_channel_id", "") or "").strip()
        if cid.isdigit():
            target = interaction.guild.get_channel(int(cid))
    if target is None:
        await interaction.followup.send("공지 채널을 지정해주세요. (슬래시 채널 옵션 or 대시보드 announce_channel_id)", ephemeral=True)
        return
    override = {}
    if title:
        override["announce_title"] = title
    if message:
        override["announce_message"] = message
    if mention is not None:
        override["announce_mention"] = mention.value
    em = tu.build_announce(s, override)
    mtxt = tu.announce_mention_text(s, interaction.guild, override)
    try:
        sent = await target.send(content=(mtxt or None), embed=em)
    except Exception as e:
        await interaction.followup.send(f"공지 실패: {e}", ephemeral=True)
        return
    store.append_notice({"title": em.title, "message": (message or s.get("announce_message", "")),
                         "channel_id": target.id, "message_id": sent.id,
                         "by": str(interaction.user), "at": tu.now_kst_str()})
    await interaction.followup.send(f"공지 발송 완료! {target.mention}", ephemeral=True)


@bot.tree.command(name="dm-test", description="Send test DM to yourself (admin)")
async def dm_test_cmd(interaction: discord.Interaction):
    if not _is_admin_interaction(interaction):
        await interaction.response.send_message("Admin only.", ephemeral=True)
        return
    ok = await tu.send_dm(interaction.user, "DM 테스트", "DM이 정상적으로 도착하면 설정 완료입니다 🙂")
    if ok:
        await interaction.response.send_message("DM 발송 완료! 개인 메시지를 확인해주세요.", ephemeral=True)
    else:
        await interaction.response.send_message("DM 발송 실패 — DM 차단 여부를 확인해주세요.", ephemeral=True)

def run_bot(token):
    store.init_storage()
    if not token:
        print("[bot] DISCORD_TOKEN missing")
        return
    bot.run(token)
