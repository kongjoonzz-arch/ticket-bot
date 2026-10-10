import discord
import store
from ui_modal import QuestionModal


class ProductSelectView(discord.ui.View):
    def __init__(self, products):
        super().__init__(timeout=180)
        opts = []
        for p in products[:25]:
            try:
                pr = f"{int(p.get('price', 0)):,} won"
            except Exception:
                pr = str(p.get("price", 0))
            desc = "stock %s" % (p.get("stock", "?"),)
            label = ("%s - %s" % (p.get("name", "product"), pr))[:100]
            opts.append(discord.SelectOption(label=label, value=str(p.get("id")), description=desc[:100]))
        sel = discord.ui.Select(placeholder="Select product", options=opts, custom_id="buy:product")
        sel.callback = self.on_select
        self.add_item(sel)

    async def on_select(self, interaction):
        prods = store.load_products()
        pid = interaction.data["values"][0]
        prod = next((p for p in prods if str(p.get("id")) == pid), None)
        if prod is None:
            await interaction.response.send_message("Product not found.", ephemeral=True)
            return
        await interaction.response.send_modal(QuestionModal(kind="buy", product=prod))


class PanelView(discord.ui.View):
    def __init__(self, buy_label="Buy", error_label="Error"):
        super().__init__(timeout=None)
        self.buy_btn.label = buy_label[:80]
        self.error_btn.label = error_label[:80]

    @discord.ui.button(label="Buy", emoji="\U0001F6D2", style=discord.ButtonStyle.success, custom_id="panel:buy")
    async def buy_btn(self, interaction, button):
        prods = [p for p in store.load_products() if p.get("enabled", True)]
        if not prods:
            await interaction.response.send_message("No products on sale.", ephemeral=True)
            return
        await interaction.response.send_message("Select product.", view=ProductSelectView(prods), ephemeral=True)

    @discord.ui.button(label="Error", emoji="❓", style=discord.ButtonStyle.secondary, custom_id="panel:error")
    async def error_btn(self, interaction, button):
        await interaction.response.send_modal(QuestionModal(kind="error"))

