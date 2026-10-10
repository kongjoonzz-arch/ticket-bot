import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import store
import ticket_utils as tu

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = os.getenv("GUILD_ID", "")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)


def panel_embed():
    s = store.load_settings()
    color = s.get("panel_color", 5814783)
    try:
        color = int(color)
    except Exception:
        color = 5814783
    em = discord.Embed(title=s.get("panel_title", "Ticket"),
                       description=s.get("panel_description", ""),
                       color=color)
    prods = [p for p in store.load_products() if p.get("enabled", True)]
    if prods:
        lines = []
        for p in prods[:20]:
            try:
                pr = f"{int(p.get('price', 0)):,}won"
            except Exception:
                pr = str(p.get("price", 0))
            lines.append(f"**{p.get('name')}** - {pr} (stock {p.get('stock', '?')})")
        em.add_field(name="Products", value="\n".join(lines), inline=False)
    foot = s.get("panel_footer", "")
    if foot:
        em.set_footer(text=foot)
    img = (s.get("panel_image_url") or "").strip()
    if img.startswith("http"):
        em.set_image(url=img)
    return em
