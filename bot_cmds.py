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
    from ui_close import ClosedTicketView
    bot.add_view(ClosedTicketView(str(s.get("delete_button_label", "🗑️ 채널 삭제") or "🗑️ 채널 삭제")))
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
    product = str(info.get("product") or "").strip()
    category = str(info.get("category") or "").strip() or "기타"
    guild_id = info.get("guild_id")
    guild = bot.get_guild(int(guild_id)) if guild_id else None
    star_txt = "⭐" * max(1, min(5, stars))
    fmt = str(s.get("review_title_format", "⭐ {stars} · {user}") or "")
    title = tu.fill(fmt, {"stars": star_txt, "user": str(message.author), "no": ticket_no})
    avatar = ""
    try:
        _av = getattr(message.author, "display_avatar", None)
        avatar = _av.url if _av is not None else ""
    except Exception:
        avatar = ""
    if guild is not None:
        import ui_receipt
        ctx_r = {
            "title": title or "⭐ 고객 후기",
            "user": str(message.author),
            "stars": stars,
            "star_txt": star_txt,
            "product": product or "상품",
            "category": category,
            "ticket_no": ticket_no,
            "text": text,
            "at": tu.now_kst_str(),
            "avatar": avatar,
        }
        sent = await ui_receipt.send_review_card(guild, s, ctx_r)
        try:
            rec = {"ticket_no": ticket_no, "user_id": message.author.id,
                   "user_name": str(message.author), "stars": stars,
                   "product": product, "category": category,
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


@bot.tree.command(name="상품지급", description="상품 내용을 대상에게 DM 카드로 지급합니다 (관리자)")
@app_commands.describe(member="지급 받을 사람 (티켓 채널에서는 자동 지정)",
                       product="상품 이름",
                       content="짧은 내용 (긴 내용은 비우고 입력창/파일 사용)",
                       file="긴 텍스트 파일 첨부 (txt/md · 줄바꿈 그대로 전송)")
async def give_product_cmd(interaction: discord.Interaction, member: discord.Member = None,
                           product: str = "", content: str = "",
                           file: discord.Attachment = None):
    s = store.load_settings()
    if not tu.is_admin(interaction.user, s):
        await interaction.response.send_message(embed=tu.err_embed("관리자만 사용할 수 있어요."), ephemeral=True)
        return
    if member is None:
        # 티켓 채널에서 실행하면 티켓 주인에게 자동 지급
        cid = getattr(interaction.channel, "id", 0)
        for tk in store.load_tickets():
            if tk.get("channel_id") == cid and tk.get("user_id"):
                try:
                    member = interaction.guild.get_member(int(tk["user_id"]))
                except Exception:
                    member = None
                break
    if member is None:
        await interaction.response.send_message(
            embed=tu.err_embed("지급 대상(`member`)을 지정해주세요.\n티켓 채널에서 실행하면 자동으로 지정됩니다."),
            ephemeral=True)
        return
    text = (content or "").strip()
    if file is not None and not text:
        try:
            raw = await file.read()
        except Exception as e:
            await interaction.response.send_message(embed=tu.err_embed(f"파일 읽기 실패: {e}"), ephemeral=True)
            return
        try:
            text = raw.decode("utf-8")
        except Exception:
            text = raw.decode("utf-8", errors="replace")
        if not text.strip():
            await interaction.response.send_message(
                embed=tu.err_embed("파일에 내용이 없어요. (txt/md 파일을 올려주세요)"), ephemeral=True)
            return
    if not text:
        from ui_gift import ProductGiveModal
        await interaction.response.send_modal(ProductGiveModal(member, product))
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    from ui_gift import send_product_dm, log_gift, normalize_text
    ok, msg = await send_product_dm(member, product, text, admin_name=str(interaction.user))
    try:
        await log_gift(interaction.guild, s, interaction.user, member, product,
                       len(normalize_text(text)), ok, msg)
    except Exception:
        pass
    if ok:
        em = tu.ok_embed("🎁 상품 지급 완료",
                         f"{member.mention} 님에게 DM을 보냈습니다.\n> {msg}", color=0x57F287)
    else:
        em = tu.err_embed(f"상품 지급 실패\n{msg}")
    try:
        await interaction.followup.send(embed=em, ephemeral=True)
    except Exception:
        pass


@bot.tree.command(name="역할테스트", description="구매자 역할 지급이 가능한지 점검합니다 (관리자)")
@app_commands.describe(member="점검할 대상 (비우면 본인)")
async def role_test_cmd(interaction: discord.Interaction, member: discord.Member = None):
    s = store.load_settings()
    if not tu.is_admin(interaction.user, s):
        await interaction.response.send_message(embed=tu.err_embed("관리자만 사용할 수 있어요."), ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild
    member = member or interaction.user
    rid = str(s.get("buyer_role_id") or "").strip()
    lines = []
    ok_all = True
    me = guild.me
    role = None
    if not rid:
        lines.append("❌ 대시보드 `buyer_role_id` 가 비어 있습니다")
        ok_all = False
    elif not rid.isdigit():
        lines.append("❌ `buyer_role_id` 가 숫자 ID가 아닙니다")
        ok_all = False
    else:
        role = guild.get_role(int(rid))
        lines.append(("✅" if role else "❌") + f" 역할 조회: {role.mention if role else '없음(잘못된 ID)'}")
        if role is None:
            ok_all = False
    has_perm = bool(getattr(getattr(me, "guild_permissions", None), "manage_roles", False))
    lines.append(("✅" if has_perm else "❌") + " 봇 '역할 관리' 권한")
    if not has_perm:
        ok_all = False
    if role is not None and me is not None:
        higher = getattr(me.top_role, "position", 0) > getattr(role, "position", 0)
        lines.append(("✅" if higher else "❌")
                     + f" 역할 서열: 봇 최상위 {getattr(me.top_role, 'position', 0)} / 대상 {getattr(role, 'position', 0)}")
        if not higher:
            ok_all = False
    if role is not None and ok_all:
        try:
            await member.add_roles(role, reason="역할 지급 점검")
            removed = True
            try:
                await member.remove_roles(role, reason="역할 지급 점검 원복")
            except Exception:
                removed = False
            lines.append("✅ 실제 지급 테스트 성공" + ("" if removed else " (원복 실패 · 역할이 남을 수 있음)"))
        except discord.Forbidden:
            ok_all = False
            lines.append("❌ 지급 실패: 권한 부족(403)")
        except Exception as e:
            ok_all = False
            lines.append(f"❌ 지급 실패: {e}")
    text = "\n".join(lines)
    em = tu.ok_embed("🧪 역할 지급 점검 · 성공", text, color=0x57F287) if ok_all else tu.err_embed(text)
    em.add_field(name="대상", value=getattr(member, "mention", str(member)), inline=True)
    await interaction.followup.send(embed=em, ephemeral=True)


def _stock_choices(current):
    out = []
    cur = str(current or "").lower()
    for p in store.load_products():
        name = str(p.get("name") or "")
        if cur and cur not in name.lower():
            continue
        try:
            st = int(p.get("stock", 0) or 0)
        except Exception:
            st = 0
        label = f"{name} · 재고 {'무제한' if st < 0 else st}개"
        out.append(app_commands.Choice(name=label[:100], value=str(p.get("id"))))
        if len(out) >= 25:
            break
    return out


async def _stock_ac(interaction: discord.Interaction, current: str):
    try:
        return _stock_choices(current)
    except Exception:
        return []


@bot.tree.command(name="재고추가", description="상품 재고를 추가하고 입고 알림을 보냅니다 (관리자)")
@app_commands.describe(product="상품 (이름으로 검색)", amount="추가할 수량")
@app_commands.autocomplete(product=_stock_ac)
async def add_stock_cmd(interaction: discord.Interaction, product: str,
                        amount: app_commands.Range[int, 1, 100000]):
    import asyncio as _aio
    s = store.load_settings()
    if not tu.is_admin(interaction.user, s):
        await interaction.response.send_message(embed=tu.err_embed("관리자만 사용할 수 있어요."), ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    prods = store.load_products()
    prod = next((p for p in prods if str(p.get("id")) == str(product)), None)
    if prod is None:
        prod = next((p for p in prods if str(p.get("name")) == str(product)), None)
    if prod is None:
        await interaction.followup.send(embed=tu.err_embed("상품을 찾을 수 없어요."), ephemeral=True)
        return
    try:
        cur = int(prod.get("stock", 0) or 0)
    except Exception:
        cur = 0
    if cur < 0:
        cur = 0
    ok, new = store.set_stock(prod.get("id"), cur + int(amount))
    if not ok:
        await interaction.followup.send(embed=tu.err_embed("재고 변경에 실패했어요."), ephemeral=True)
        return
    from ui_stock import send_restock, restock_channel_id
    item = [{"name": prod.get("name"), "category": prod.get("category"),
             "added": int(amount), "stock": new}]
    try:
        sent = await _aio.to_thread(send_restock, s, item, f"/재고추가 · {interaction.user}")
    except Exception as e:
        print(f"[stock] notify failed: {e}")
        sent = False
    ch_id = restock_channel_id(s)
    note = ("입고 알림 전송 완료" if sent
            else ("입고 채널 ID가 없어 알림을 못 보냈어요 (대시보드 `stock_log_channel_id` 설정)"
                  if not ch_id else "입고 알림 전송 실패 (봇 권한/토큰 확인)"))
    em = tu.ok_embed("📦 재고 추가 완료",
                     f"**{prod.get('name')}**\n추가: **+{int(amount)}개** · 현재 **{new}개**\n> {note}",
                     color=0x57F287)
    await interaction.followup.send(embed=em, ephemeral=True)


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
    keep = bool(s.get("close_keep_channel", True))
    await do_close_ticket(interaction.guild, interaction.channel, interaction.user, reason)
    try:
        em = discord.Embed(title="🔒 티켓 닫기 완료", color=0xED4245)
        tail = ("이 채널은 이제 **관리자에게만** 보입니다.\n삭제하려면 **🗑️ 채널 삭제** 버튼을 눌러주세요."
                if keep else "채널이 곧 삭제됩니다.")
        em.description = f"사유: {reason or '사유 미입력'}\n{tail}"
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
