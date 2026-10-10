# -*- coding: utf-8 -*-
# UNUSED legacy file (broken encoding) - safe to delete. (ui_modal.py 사용)

import discord
import store
import ticket_utils as tu


# ---------- 질문 모달 (?�?�보??질문 ???�적 ?�성, 최�? 5�? ----------

class QuestionModal(discord.ui.Modal):
    def __init__(self, kind: str, product=None):
        questions = store.load_questions()
        qlist = [q for q in questions.get(kind, []) if q.get("enabled", True)][:5]
        title = "?�� 구매문의 ?�성" if kind == "buy" else "???�류문의 ?�성"
        super().__init__(title=title[:45])
        self.kind = kind
        self.product = product
        self.qlist = qlist
        for q in qlist:
            self.add_item(discord.ui.TextInput(
                label=str(q.get("label", "질문"))[:45],
                placeholder=str(q.get("placeholder", ""))[:100] or None,
                required=bool(q.get("required", True)),
                max_length=int(q.get("max_length", 300) or 300),
                style=discord.TextStyle.paragraph if int(q.get("max_length", 100) or 100) > 100 else discord.TextStyle.short,
                custom_id=str(q.get("id", "q")),
            ))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        settings = store.load_settings()
        guild = interaction.guild
        user = interaction.user
        answers = []
        for item, q in zip(self.children, self.qlist):
            answers.append({"id": q.get("id"), "label": q.get("label"),
                            "value": item.value or ""})

        tickets = store.load_tickets()
        ticket_no = (max([t.get("no", 0) for t in tickets]) + 1) if tickets else 1

        try:
            channel = await tu.create_ticket_channel(guild, user, self.kind, ticket_no, settings)
        except discord.Forbidden:
            await interaction.followup.send("??채널 ?�성 권한???�어?? 봇에�?**채널 관�?* 권한??주세??", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"??채널 ?�성 ?�패: {e}", ephemeral=True)
            return

        summary = tu.build_summary_embed(self.kind, user, self.product, answers, ticket_no)

        mention_txt = ""
        if settings.get("mention_admin_on_create"):
            raw = settings.get("mention_text", "") or ""
            mention_txt = raw.replace("{admin_mention}",
                                      tu.admin_mention_text(settings, guild)) + "\n"
        welcome = (settings.get("welcome_message") or "").replace("{user_mention}", user.mention)
        try:
            await channel.send(mention_txt + welcome, embed=summary, view=TicketControlView())
        except Exception as e:
            print(f"[ticket] �?메시지 ?�송 ?�패: {e}")

        tickets.append({
            "no": ticket_no, "kind": self.kind,
            "user_id": user.id, "user_name": str(user),
            "channel_id": channel.id,
            "product": self.product,
            "answers": answers, "status": "open",
            "created_at": tu.now_kst_str(),
        })
        store.save_tickets(tickets)

        log = discord.Embed(title=f"?�� ?�켓 #{ticket_no} ?�성",
                            description=f"{user.mention} | {'구매문의' if self.kind == 'buy' else '?�류문의'} | {channel.mention}",
                            color=0x5865F2)
        await tu.send_log(guild, settings, log)
        await interaction.followup.send(f"???�켓???�렸?�요! {channel.mention} ?�서 ?�어??문의?�주?�요.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        print(f"[modal] ?�류: {error}")
        try:
            await interaction.followup.send("???�켓 ?�성 �??�류가 발생?�어??", ephemeral=True)
        except Exception:
            pass


# ---------- ?�품 ?�택 ----------

class ProductSelectView(discord.ui.View):
    def __init__(self, products: list):
        super().__init__(timeout=180)
        options = []
        for p in products[:25]:
            price = p.get("price", 0)
            try:
                price_txt = f"{int(price):,}??
            except Exception:
                price_txt = str(price)
            options.append(discord.SelectOption(
                label=f"{p.get('name', '?�품')} ??{price_txt}"[:100],
                value=str(p.get("id")),
                description=f"?�고 {p.get('stock', '?')} | {str(p.get('description', ''))[:50]}"[:100],
            ))
        sel = discord.ui.Select(placeholder="구매???�품???�택?�세??, options=options, custom_id="buy:product")
        sel.callback = self.on_select
        self.add_item(sel)

    async def on_select(self, interaction: discord.Interaction):
        products = store.load_products()
        pid = interaction.data["values"][0]
        product = next((p for p in products if str(p.get("id")) == pid), None)
        if product is None:
            await interaction.response.send_message("???�당 ?�품??찾을 ???�어??", ephemeral=True)
            return
        await interaction.response.send_modal(QuestionModal(kind="buy", product=product))
# ---------- ?�널 (?�구 View: ?�시???�에???�작) ----------

class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="구매문의", emoji="?��", style=discord.ButtonStyle.success, custom_id="panel:buy")
    async def buy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        products = [p for p in store.load_products() if p.get("enabled", True)]
        if not products:
            await interaction.response.send_message(
                "???�재 ?�매 중인 ?�품???�어?? 관리자?�게 문의?�주?�요.", ephemeral=True)
            return
        await interaction.response.send_message(
            "?�� 구매???�품???�택?�주?�요.", view=ProductSelectView(products), ephemeral=True)

    @discord.ui.button(label="?�류문의", emoji="??, style=discord.ButtonStyle.secondary, custom_id="panel:error")
    async def error_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(QuestionModal(kind="error"))

# -*- coding: utf-8 -*-
"""?�켓 ?��? 관�?버튼 (구매?�인/?�기 = 관리자�?."""
import discord
import store
import ticket_utils as tu


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _guard_admin(self, interaction: discord.Interaction) -> bool:
        settings = store.load_settings()
        if tu.is_admin(interaction.user, settings):
            return True
        await interaction.response.send_message(
            "????버튼?� **관리자�?* ?�용?????�어??", ephemeral=True)
        return False

    def _find_ticket(self, channel_id: int):
        for t in store.load_tickets():
            if t.get("channel_id") == channel_id:
                return t
        return None

    @discord.ui.button(label="??구매?�인", style=discord.ButtonStyle.success,
                       custom_id="ticket:confirm")
    async def confirm_btn(self, interaction: discord.Interaction,
                          button: discord.ui.Button):
        if not await self._guard_admin(interaction):
            return
        t = self._find_ticket(interaction.channel_id)
        status = f" (?�재: {t.get('status')})" if t else ""
        await interaction.response.send_message(
            f"??관리자가 **구매�??�인**?�습?�다.{status}\n"
            "?�금 ?�인 ???�품???�달?�주?�요!")

    @discord.ui.button(label="?�� ?�켓?�기", style=discord.ButtonStyle.danger,
                       custom_id="ticket:close")
    async def close_btn(self, interaction: discord.Interaction,
                        button: discord.ui.Button):
        if not await self._guard_admin(interaction):
            return
        settings = store.load_settings()
        await interaction.response.send_message(
            settings.get("close_message", "?�� ?�켓???�혔?�니??"))
        tickets = store.load_tickets()
        for t in tickets:
            if t.get("channel_id") == interaction.channel_id:
                t["status"] = "closed"
                t["closed_at"] = tu.now_kst_str()
        store.save_tickets(tickets)
        log = discord.Embed(
            title="?�� ?�켓 ?�힘",
            description=f"{interaction.channel.mention} | ?�당: {interaction.user.mention}",
            color=0xED4245)
        await tu.send_log(interaction.guild, settings, log)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True),
        }
        try:
            await interaction.channel.edit(overwrites=overwrites, reason="?�켓 ?�기 (관리자)")
        except Exception as e:
            print(f"[ticket] 채널 ?�금 ?�패: {e}")
