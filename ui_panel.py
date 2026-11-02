import discord
import store
from ui_modal import QuestionModal
import ticket_utils as tu


def _price(p):
    try:
        return f"{int(p.get('price', 0)):,}원"
    except Exception:
        return str(p.get("price", ""))


def category_of(product):
    """상품 카테고리 (없으면 '기타')."""
    return str((product or {}).get("category") or "").strip() or "기타"


def group_by_category(products):
    groups = {}
    for p in sort_products(products):
        groups.setdefault(category_of(p), []).append(p)
    return {c: groups[c] for c in sort_categories(list(groups.keys()))}


def sort_products(products):
    """상품을 order(낮을수록 먼저) → 이름 순으로 정렬."""
    def key(p):
        try:
            o = int(p.get("order", 0) or 0)
        except Exception:
            o = 0
        return (o if o > 0 else 10 ** 6, str(p.get("name") or ""))
    return sorted(products or [], key=key)


def sort_categories(names):
    """저장된 카테고리 순서대로 정렬 (목록에 없는 카테고리는 뒤로)."""
    try:
        order = store.load_category_order()
    except Exception:
        order = []
    idx = {c: i for i, c in enumerate(order)}
    return sorted(names, key=lambda c: (idx.get(c, len(order) + 1), c))


def _color(settings=None):
    s = settings or store.load_settings()
    try:
        return int(s.get("panel_color", 0x5865F2))
    except Exception:
        return 0x5865F2


def stock_of(product):
    try:
        return int((product or {}).get("stock", 0) or 0)
    except Exception:
        return 0


def stock_enabled(settings=None):
    s = settings if settings is not None else store.load_settings()
    v = s.get("stock_enabled", True)
    if isinstance(v, str):
        return v.strip().lower() == "true"
    return bool(v)


def is_sold_out(product, settings=None):
    """재고 0 = 품절 / 재고 음수 = 무제한 / 재고관리 off = 항상 판매중."""
    if not stock_enabled(settings):
        return False
    return stock_of(product) == 0


def stock_text(product, settings=None):
    if not stock_enabled(settings):
        return "재고 무제한"
    n = stock_of(product)
    if n < 0:
        return "재고 무제한"
    if n == 0:
        return "품절"
    return f"재고 {n}"


def available(products, settings=None):
    """판매 가능한 상품만 (판매중 + 품절 아님)."""
    s = settings if settings is not None else store.load_settings()
    return [p for p in (products or []) if p.get("enabled", True) and not is_sold_out(p, s)]


def build_category_embed(products, settings=None):
    em = discord.Embed(title="🏷️ 상품 카테고리", color=_color(settings))
    em.description = "━━━━━━━━━━━━━━━\n원하시는 카테고리를 골라주세요.\n━━━━━━━━━━━━━━━"
    for cat, items in group_by_category(products).items():
        prices = []
        for p in items:
            try:
                prices.append(int(p.get("price", 0)))
            except Exception:
                pass
        price_txt = f"최저 {min(prices):,}원" if prices else "-"
        em.add_field(name=cat, value=f"📦 {len(items)}개 상품\n💰 {price_txt}", inline=True)
    em.set_footer(text="카테고리 → 상품 선택 → 질문 작성 순서로 진행됩니다")
    return em


def build_product_embed(products, category=None, settings=None):
    title = "🎁 상품 선택" if not category else f"🎁 {category} · 상품 선택"
    em = discord.Embed(title=title, color=_color(settings))
    em.description = "━━━━━━━━━━━━━━━\n구매할 상품을 아래 목록에서 골라주세요.\n━━━━━━━━━━━━━━━"
    for p in sort_products(products)[:10]:
        em.add_field(
            name=f"{p.get('name')} · {_price(p)}",
            value=f"🏷️ {category_of(p)}\n📦 {stock_text(p, settings)}\n> {str(p.get('description', '') or '')[:120]}",
            inline=False)
    em.set_footer(text="선택 후 질문을 작성하면 전용 티켓이 열립니다")
    return em


class CategorySelectView(discord.ui.View):
    def __init__(self, products):
        super().__init__(timeout=180)
        opts = []
        for cat, items in group_by_category(products).items():
            try:
                cheap = min(int(p.get("price", 0)) for p in items)
                price = f" · {cheap:,}원~"
            except Exception:
                price = ""
            opts.append(discord.SelectOption(label=cat[:100], value=cat[:100],
                                             description=f"{len(items)}개 상품{price}"[:100]))
        sel = discord.ui.Select(placeholder="🏷️ 카테고리를 선택하세요", options=opts[:25],
                               custom_id="buy:category")
        sel.callback = self.on_select
        self.add_item(sel)

    async def on_select(self, interaction):
        cat = interaction.data["values"][0]
        s = store.load_settings()
        prods = [p for p in store.load_products()
                 if p.get("enabled", True) and category_of(p) == cat and not is_sold_out(p, s)]
        if not prods:
            await interaction.response.send_message(
                embed=tu.err_embed("해당 카테고리 상품이 모두 품절이에요."), ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_product_embed(prods, cat),
                                               view=ProductSelectView(prods, category=cat))


class ProductSelectView(discord.ui.View):
    def __init__(self, products, category=None):
        super().__init__(timeout=180)
        self.category = category
        opts = []
        for p in sort_products(products)[:25]:
            desc = f"🏷️ {category_of(p)} · {stock_text(p)}"
            opts.append(discord.SelectOption(label=f"{p.get('name', '상품')} · {_price(p)}"[:100],
                                             value=str(p.get("id")),
                                             description=desc[:100]))
        sel = discord.ui.Select(placeholder="🎁 구매할 상품을 선택하세요", options=opts,
                               custom_id="buy:product")
        sel.callback = self.on_select
        self.add_item(sel)
        if category:
            back = discord.ui.Button(label="⬅️ 카테고리", style=discord.ButtonStyle.secondary, row=1)
            back.callback = self.go_back
            self.add_item(back)

    async def go_back(self, interaction):
        prods = available(store.load_products())
        await interaction.response.edit_message(embed=build_category_embed(prods),
                                               view=CategorySelectView(prods))

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
        s = store.load_settings()
        allp = [p for p in store.load_products() if p.get("enabled", True)]
        prods = available(allp, s)
        if not prods:
            msg = ("지금은 모든 상품이 **품절**이에요. 조금 뒤에 다시 시도해주세요."
                   if allp else "현재 판매 중인 상품이 없어요.")
            await interaction.response.send_message(embed=tu.err_embed(msg), ephemeral=True)
            return
        if len(group_by_category(prods)) > 1:
            em = build_category_embed(prods, s)
            await interaction.response.send_message(embed=em, view=CategorySelectView(prods), ephemeral=True)
            return
        em = build_product_embed(prods, settings=s)
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

