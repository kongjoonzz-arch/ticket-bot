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
        answers = []
        for item, q in zip(self.children, self.qlist):
            answers.append({"id": q.get("id"), "label": q.get("label"), "value": item.value or ""})
        ticket_no = store.next_ticket_no()
        try:
            channel = await tu.create_ticket_channel(guild, user, self.kind, ticket_no, settings)
        except discord.Forbidden:
            await interaction.followup.send("No permission to create channel.", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"Channel create failed: {e}", ephemeral=True)
            return
        summary = tu.build_summary_embed(self.kind, user, self.product, answers, ticket_no)
        mention_txt = ""
        if settings.get("mention_admin_on_create"):
            raw = settings.get("mention_text", "") or ""
            mention_txt = raw.replace("{admin_mention}", tu.admin_mention_text(settings, guild)) + "\n"
        welcome = (settings.get("welcome_message") or "").replace("{user_mention}", user.mention)
        from ui_control import TicketControlView
        try:
            await channel.send(mention_txt + welcome, embed=summary, view=TicketControlView())
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
            ok = await tu.send_dm(user, title, msg)
            if not ok:
                try:
                    await channel.send(f"{user.mention} DM이 차단되어 있어 채널로 안내드립니다. DM 차단을 풀어주세요 🙂")
                except Exception:
                    pass
        log = discord.Embed(title=f"Ticket #{ticket_no} created", description=f"{user.mention} | {self.kind} | {channel.mention}", color=0x5865F2)
        await tu.send_log(guild, settings, log)
        await interaction.followup.send(f"Ticket opened! {channel.mention}", ephemeral=True)
