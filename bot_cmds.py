import discord
from discord import app_commands
import store
import ticket_utils as tu
from ui_panel import make_panel_view
from ui_control import TicketControlView
from bot_main import bot, build_panel_embed, send_panel_message, GUILD_ID_INT

@bot.event
async def on_ready():
    print(f"[bot] logged in as {bot.user}")
    s = store.load_settings()
    bot.add_view(make_panel_view(s))
    bot.add_view(TicketControlView(str(s.get("ticket_button_label", "🔒 티켓 닫기") or "🔒 티켓 닫기"),
                                   str(s.get("complete_button_label", "✅ 구매완료") or "✅ 구매완료")))
    from ui_review import ReviewStarsView
    bot.add_view(ReviewStarsView(0, 0))
    try:
        from custom_cmds import sync_custom_commands
        if GUILD_ID_INT:
            g = discord.Object(id=GUILD_ID_INT)
            names = sync_custom_commands(bot.tree, g)
            bot.tree.copy_global_to(guild=g)
            synced = await bot.tree.sync(guild=g)
            print(f"[bot] synced {len(synced)} cmds to guild {GUILD_ID_INT} (custom: {names})")
        else:
            names = sync_custom_commands(bot.tree, None)
            synced = await bot.tree.sync()
            print(f"[bot] synced {len(synced)} global cmds (custom: {names})")
    except Exception as e:
        print(f"[bot] sync failed: {e}")

def _is_admin_interaction(interaction):
    s = store.load_settings()
    return tu.is_admin(interaction.user, s)


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel):
        try:
            await handle_review_dm(message)
        except Exception as e:
            print(f"[review] dm handle failed: {e}")
    try:
        await bot.process_commands(message)
    except Exception:
        pass


async def handle_review_dm(message):
    import json as _j
    import os as _o
    pp = _o.path.join(store.DATA_DIR, "review_pending.json")
    if not _o.path.exists(pp):
        return
    try:
        with open(pp, "r", encoding="utf-8") as f:
            cur = _j.load(f)
    except Exception:
        return
    key = str(message.author.id)
    if key not in cur:
        return
    text = (message.content or "").strip()
    s = store.load_settings()
    need = int(s.get("review_min_length", 5) or 5)
    if len(text) < need:
        try:
            await message.author.send(embed=tu.err_embed(f"후기가 너무 짧아요. **{need}자 이상** 적어주세요 🙂"))
        except Exception:
            pass
        return
    info = cur.pop(key, {})
    try:
        with open(pp, "w", encoding="utf-8") as f:
            _j.dump(cur, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    stars = int(info.get("stars", 5) or 5)
    ticket_no = info.get("ticket_no", "?")
    guild_id = info.get("guild_id")
    guild = bot.get_guild(int(guild_id)) if guild_id else None
    star_txt = "⭐" * max(1, min(5, stars))
    fmt = str(s.get("review_title_format", "⭐ {stars} · {user}") or "")
    title = tu.fill(fmt, {"stars": star_txt, "user": str(message.author), "no": ticket_no})
    em = tu.apex_embed(s, title, text, color=0xFEE75C)
    em.add_field(name="🎫 티켓", value=f"#{ticket_no}", inline=True)
    em.add_field(name="⭐ 별점", value=f"{star_txt} ({stars}/5)", inline=True)
    em.set_footer(text=f"{tu.BOT_NAME} · {tu.now_kst_str()} (KST)")
    try:
        avatar = getattr(message.author, "display_avatar", None)
        if avatar is not None:
            em.set_thumbnail(url=avatar.url)
    except Exception:
        pass
    if guild is not None:
        sent = await tu.send_review(guild, s, em)
        try:
            rec = {"ticket_no": ticket_no, "user_id": message.author.id,
                   "user_name": str(message.author), "stars": stars,
                   "text": text, "at": tu.now_kst_str()}
            import json as _j2, os as _o2
            rp = _o2.path.join(store.DATA_DIR, "reviews.json")
            arr = []
            if _o2.path.exists(rp):
                with open(rp, "r", encoding="utf-8") as f:
                    arr = _j2.load(f)
            arr.append(rec)
            with open(rp, "w", encoding="utf-8") as f:
                _j2.dump(arr, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[review] save failed: {e}")
        if sent is not None:
            try:
                await message.author.send(embed=tu.ok_embed("✅ 후기 등록 완료", "소중한 후기 감사합니다! 후기 채널에 등록됐어요 🎉", color=0x57F287))
            except Exception:
                pass
        else:
            try:
                await message.author.send(embed=tu.err_embed("후기 채널이 설정되지 않았어요. 관리자에게 문의해주세요."))
            except Exception:
                pass
    else:
        try:
            await message.author.send(embed=tu.err_embed("서버 정보를 찾을 수 없어요."))
        except Exception:
            pass

@bot.tree.command(name="panel", description="Send ticket panel to this channel (admin)")
async def panel_cmd(interaction: discord.Interaction):
    if not _is_admin_interaction(interaction):
        await interaction.response.send_message(embed=tu.err_embed("관리자만 사용할 수 있어요."), ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        mode, _m = await send_panel_message(interaction.channel)
    except Exception as e:
        await interaction.followup.send(embed=tu.err_embed(f"패널 실패: {e}"), ephemeral=True)
        return
    txt = "V2 컨테이너(임베드 안 버튼)로 전송" if mode == "v2" else "기존 임베드+버튼으로 전송"
    done = discord.Embed(title="✅ 패널 전송 완료", description=f"{txt}했습니다.", color=0x57F287)
    await interaction.followup.send(embed=done, ephemeral=True)


@bot.event
async def on_interaction(interaction):
    try:
        if interaction.type == discord.InteractionType.component:
            cid = ""
            try:
                cid = str((interaction.data or {}).get("custom_id", ""))
            except Exception:
                cid = ""
            if cid == "panel:buy":
                from ui_panel import PanelView
                s = store.load_settings()
                pv = make_panel_view(s)
                for child in pv.children:
                    if getattr(child, "custom_id", "") == "panel:buy":
                        await child.callback(interaction)
                        return
            elif cid == "panel:error":
                s = store.load_settings()
                pv = make_panel_view(s)
                for child in pv.children:
                    if getattr(child, "custom_id", "") == "panel:error":
                        await child.callback(interaction)
                        return
    except Exception as e:
        print(f"[v2] component route failed: {e}")

@bot.tree.command(name="cmd-reload", description="Reload dashboard custom commands (admin)")
async def cmd_reload(interaction: discord.Interaction):
    if not _is_admin_interaction(interaction):
        await interaction.response.send_message(embed=tu.err_embed("관리자만 사용할 수 있어요."), ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        from custom_cmds import sync_custom_commands
        from bot_main import GUILD_ID_INT as _gid
        if _gid:
            g = discord.Object(id=_gid)
            names = sync_custom_commands(bot.tree, g)
            bot.tree.copy_global_to(guild=g)
            await bot.tree.sync(guild=g)
        else:
            names = sync_custom_commands(bot.tree, None)
            await bot.tree.sync()
        em = tu.ok_embed("✅ 명령어 동기화", "등록됨:\n" + ("\n".join([f"• `/{n}`" for n in names]) if names else "없음"), color=0x57F287)
        await interaction.followup.send(embed=em, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=tu.err_embed(f"동기화 실패: {e}"), ephemeral=True)


@bot.tree.command(name="구매완료", description="구매완료 처리: 역할지급+구매로그+후기DM (관리자)")
async def complete_cmd(interaction: discord.Interaction):
    s = store.load_settings()
    if not tu.is_admin(interaction.user, s):
        await interaction.response.send_message(embed=tu.err_embed("관리자만 사용할 수 있어요."), ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=False)
    from ui_done import do_complete_ticket
    ok, msg = await do_complete_ticket(interaction.guild, interaction.channel, interaction.user)
    em = tu.ok_embed("✅ 구매완료", msg, color=0x57F287) if ok else tu.err_embed(msg)
    try:
        await interaction.followup.send(embed=em, ephemeral=True)
    except Exception:
        pass


@bot.tree.command(name="ticket-close", description="Close this ticket (admin)")
@app_commands.describe(reason="Close reason (sent to channel, log and user DM)")
async def close_cmd(interaction: discord.Interaction, reason: str = ""):
    s = store.load_settings()
    if not tu.is_admin(interaction.user, s):
        await interaction.response.send_message(embed=tu.err_embed("관리자만 사용할 수 있어요."), ephemeral=True)
        return
    if not reason and bool(s.get("close_reason_required", False)):
        from ui_close import CloseReasonModal
        await interaction.response.send_modal(CloseReasonModal())
        return
    await interaction.response.defer(ephemeral=True, thinking=False)
    from ui_close import do_close_ticket
    await do_close_ticket(interaction.guild, interaction.channel, interaction.user, reason)
    try:
        em = discord.Embed(title="🔒 티켓 닫기 완료", color=0xED4245)
        em.description = f"사유: {reason or '사유 미입력'}\n채널이 곧 삭제됩니다."
        await interaction.followup.send(embed=em, ephemeral=True)
    except Exception:
        pass


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
        await interaction.response.send_message(embed=tu.err_embed("관리자만 사용할 수 있어요."), ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    target = channel
    if target is None:
        cid = str(s.get("announce_channel_id", "") or "").strip()
        if cid.isdigit():
            target = interaction.guild.get_channel(int(cid))
    if target is None:
        await interaction.followup.send(embed=tu.err_embed("공지 채널을 지정해주세요. (슬래시 채널 옵션 or 대시보드 announce_channel_id)"), ephemeral=True)
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
        await interaction.followup.send(embed=tu.err_embed(f"공지 실패: {e}"), ephemeral=True)
        return
    store.append_notice({"title": em.title, "message": (message or s.get("announce_message", "")),
                         "channel_id": target.id, "message_id": sent.id,
                         "by": str(interaction.user), "at": tu.now_kst_str()})
    done = discord.Embed(title="📢 공지 발송 완료", description=f"{target.mention} 에 공지를 올렸습니다.", color=0x57F287)
    await interaction.followup.send(embed=done, ephemeral=True)


@bot.tree.command(name="dm-test", description="Send test DM to yourself (admin)")
async def dm_test_cmd(interaction: discord.Interaction):
    if not _is_admin_interaction(interaction):
        await interaction.response.send_message(embed=tu.err_embed("관리자만 사용할 수 있어요."), ephemeral=True)
        return
    thumb = None
    try:
        thumb = interaction.guild.icon.url if getattr(interaction.guild, "icon", None) else None
    except Exception:
        thumb = None
    ok = await tu.send_dm(interaction.user, "📩 DM 테스트", "DM이 정상적으로 도착하면 설정 완료입니다 🙂", thumb_url=thumb)
    if ok:
        done = discord.Embed(title="✅ DM 발송 완료", description="개인 메시지를 확인해주세요.", color=0x57F287)
        await interaction.response.send_message(embed=done, ephemeral=True)
    else:
        await interaction.response.send_message(embed=tu.err_embed("DM 발송 실패 — DM 차단 여부를 확인해주세요."), ephemeral=True)

def run_bot(token):
    store.init_storage()
    if not token:
        print("[bot] DISCORD_TOKEN missing")
        return
    bot.run(token)
