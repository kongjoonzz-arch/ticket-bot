import discord
import store
from ui_modal import QuestionModal
import ticket_utils as tu


def _price(p):
    try:
        return f"{int(p.get('price', 0)):,}원"
    except Exception:
        return str(p.get("price", ""))


class ProductSelectView(discord.ui.View):
    def __init__(self, products):
        super().__init__(timeout=180)
        opts = []
        for p in products[:25]:
            desc = str(p.get("description", "") or "")[:60]
            label = f"{p.get('name', '상품')} · {_price(p)}"[:100]
            opts.append(discord.SelectOption(label=label, value=str(p.get("id")),
                                             description=f"재고 {p.get('stock', '?')} · {desc}"[:100]))
        sel = discord.ui.Select(placeholder="🎁 구매할 상품을 선택하세요", options=opts, custom_id="buy:product")
        sel.callback = self.on_select
        self.add_item(sel)

    async def on_select(self, interaction):
        prods = store.load_products()
        pid = interaction.data["values"][0]
        prod = next((p for p in prods if str(p.get("id")) == pid), None)
        if prod is None:
            await interaction.response.send_message(embed=tu.err_embed("해당 상품을 찾을 수 없어요."), ephemeral=True)
            return
        await interaction.response.send_modal(QuestionModal(kind="buy", product=prod))


class PanelView(discord.ui.View):
    def __init__(self, buy_label="구매 문의", error_label="오류 문의",
                 buy_emoji=None, error_emoji=None):
        super().__init__(timeout=None)
        self.buy_btn.label = str(buy_label or "구매 문의")[:80]
        self.error_btn.label = str(error_label or "오류 문의")[:80]
        try:
            self.buy_btn.emoji = buy_emoji
        except Exception:
            pass
        try:
            self.error_btn.emoji = error_emoji
        except Exception:
            pass

    @discord.ui.button(label="구매 문의", style=discord.ButtonStyle.primary, custom_id="panel:buy", row=0)
    async def buy_btn(self, interaction, button):
        prods = [p for p in store.load_products() if p.get("enabled", True)]
        if not prods:
            await interaction.response.send_message(embed=tu.err_embed("현재 판매 중인 상품이 없어요."), ephemeral=True)
            return
        s = store.load_settings()
        try:
            color = int(s.get("panel_color", 0x5865F2))
        except Exception:
            color = 0x5865F2
        em = discord.Embed(title="🎁 상품 선택", color=color)
        em.description = "━━━━━━━━━━━━━━━\n구매할 상품을 아래 목록에서 골라주세요.\n━━━━━━━━━━━━━━━"
        for p in prods[:10]:
            em.add_field(name=f"{p.get('name')} · {_price(p)}",
                         value=f"📦 재고 {p.get('stock', '?')}\n> {str(p.get('description', '') or '')[:120]}",
                         inline=False)
        em.set_footer(text="선택 후 질문을 작성하면 전용 티켓이 열립니다")
        await interaction.response.send_message(embed=em, view=ProductSelectView(prods), ephemeral=True)

    @discord.ui.button(label="오류 문의", style=discord.ButtonStyle.secondary, custom_id="panel:error", row=0)
    async def error_btn(self, interaction, button):
        await interaction.response.send_modal(QuestionModal(kind="error"))


def make_panel_view(settings=None):
    s = settings or store.load_settings()
    return PanelView(
        s.get("panel_button_buy", "구매 문의"),
        s.get("panel_button_error", "오류 문의"),
        tu.parse_emoji(s.get("panel_button_buy_emoji", "")),
        tu.parse_emoji(s.get("panel_button_error_emoji", "")),
    )

