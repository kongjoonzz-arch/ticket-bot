import discord
import store
import ticket_utils as tu

class QuestionModal(discord.ui.Modal):
    def __init__(self, kind, product=None):
        qs = store.load_questions()
        qlist = [q for q in qs.get(kind, []) if q.get("enabled", True)][:5]
        title = "Buy Ticket" if kind == "buy" else "Error Ticket"
        super().__init__(title=title)
        self.kind = kind
        self.product = product
        self.qlist = qlist
        for q in qlist:
            label = str(q.get("label", "Q"))[:45]
            ph = str(q.get("placeholder", ""))[:100] or None
            req = bool(q.get("required", True))
            try:
                ml = int(q.get("max_length", 200) or 200)
            except Exception:
                ml = 200
            style = discord.TextStyle.paragraph if ml > 100 else discord.TextStyle.short
            self.add_item(discord.ui.TextInput(label=label, placeholder=ph, required=req, max_length=ml, style=style))

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        settings = store.load_settings()
        guild = interaction.guild
        user = interaction.user
        if bool(settings.get("one_ticket_per_user", True)):
            dup = tu.find_open_ticket_by_user(user.id)
            if dup is not None:
                ch = guild.get_channel(dup.get("channel_id")) if dup.get("channel_id") else None
                em = tu.err_embed(f"이미 열린 티켓이 있어요.\n{(ch.mention if ch else '기존 티켓')} 에서 이어서 문의해주세요. (1인 1티켓)")
                await interaction.followup.send(embed=em, ephemeral=True)
                return
        answers = []
        for item, q in zip(self.children, self.qlist):
            answers.append({"id": q.get("id"), "label": q.get("label"), "value": item.value or ""})
        ticket_no = store.next_ticket_no()
        try:
            channel = await tu.create_ticket_channel(guild, user, self.kind, ticket_no, settings)
        except discord.Forbidden:
            await interaction.followup.send(embed=tu.err_embed("채널 생성 권한이 없어요. 봇에게 **채널 관리** 권한을 주세요."), ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(embed=tu.err_embed(f"채널 생성 실패: {e}"), ephemeral=True)
            return
        summary = tu.build_summary_embed(self.kind, user, self.product, answers, ticket_no)
        settings2 = store.load_settings()
        close_label = str(settings2.get("ticket_button_label", "🔒 티켓 닫기") or "🔒 티켓 닫기")
        from ui_control import TicketControlView
        view = TicketControlView(close_label)
        summary.add_field(name="🎛️ 티켓 관리", value="문의가 끝나면 관리자가 아래 버튼으로 티켓을 닫습니다.", inline=False)
        mention_txt = ""
        if settings.get("mention_admin_on_create"):
            raw = settings.get("mention_text", "") or ""
            mention_txt = raw.replace("{admin_mention}", tu.admin_mention_text(settings, guild))
        welcome = (settings.get("welcome_message") or "").replace("{user_mention}", user.mention)
        content = ""
        if mention_txt.strip():
            content += mention_txt.strip() + "\n"
        if welcome.strip():
            content += welcome.strip()
        try:
            await channel.send(content=content or None, embed=summary, view=view)
        except Exception as e:
            print(f"[ticket] first msg failed: {e}")
        store.append_ticket({"no": ticket_no, "kind": self.kind, "user_id": user.id, "user_name": str(user), "channel_id": channel.id, "product": self.product, "answers": answers, "status": "open", "created_at": tu.now_kst_str()})
        if settings.get("dm_on_open"):
            kind_ko = "구매문의" if self.kind == "buy" else "오류문의"
            prod_txt = ""
            if self.kind == "buy" and self.product:
                try:
                    pr = f"{int(self.product.get('price', 0)):,}원"
                except Exception:
                    pr = str(self.product.get("price", ""))
                prod_txt = f"상품: {self.product.get('name', '')} ({pr})"
            ans_txt = "\n".join([f"- {a.get('label')}: {a.get('value')}" for a in answers])[:1500]
            mapping = {"no": ticket_no, "kind": kind_ko, "user_mention": user.mention,
                       "channel": channel.mention, "product": prod_txt, "answers": ans_txt}
            title = tu.fill(settings.get("dm_open_title", ""), mapping).replace("#{no}", f"#{ticket_no}")
            msg = tu.fill(settings.get("dm_open_message", ""), mapping).replace("#{no}", f"#{ticket_no}")
            ok = await tu.send_dm(user, title, msg, thumb_url=(guild.icon.url if getattr(guild, "icon", None) else None))
            if not ok:
                try:
                    em2 = tu.ok_embed("📩 DM 알림 실패", f"{user.mention} DM이 차단되어 있어요. DM 차단을 풀어주세요 🙂", color=0xFEE75C)
                    await channel.send(embed=em2)
                except Exception:
                    pass
        log = discord.Embed(title=f"🎫 Ticket #{ticket_no} 생성", color=0x5865F2)
        log.description = "━━━━━━━━━━━━━━━"
        log.add_field(name="문의자", value=f"{user.mention} · {self.kind}", inline=False)
        log.add_field(name="채널", value=channel.mention, inline=False)
        log.set_footer(text=f"{tu.now_kst_str()} (KST)")
        log.timestamp = tu.now_kst()
        await tu.send_log(guild, settings, log)
        done = discord.Embed(title="✅ 티켓 개설 완료", color=0x57F287)
        done.description = f"{channel.mention} 에서 이어서 문의해주세요.\nDM으로도 안내를 보냈습니다."
        await interaction.followup.send(embed=done, ephemeral=True)
