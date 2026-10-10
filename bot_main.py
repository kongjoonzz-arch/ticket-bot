import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import store
import ticket_utils as tu

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = os.getenv("GUILD_ID", "0")
try:
    GUILD_ID_INT = int(GUILD_ID)
except Exception:
    GUILD_ID_INT = 0

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def build_panel_embed():
    s = store.load_settings()
    try:
        color = int(s.get("panel_color", 0x5865F2))
    except Exception:
        color = 0x5865F2
    em = discord.Embed(title=s.get("panel_title", "Ticket"), description=s.get("panel_description", ""), color=color)
    prods = [p for p in store.load_products() if p.get("enabled", True)]
    if prods:
        lines = []
        for p in prods[:20]:
            try:
                pr = f"{int(p.get('price', 0)):,} won"
            except Exception:
                pr = str(p.get("price", 0))
            lines.append(f"- {p.get('name')} : {pr} (stock {p.get('stock', '?')})")
        em.add_field(name="Products", value="\n".join(lines), inline=False)
    if s.get("panel_footer"):
        em.set_footer(text=s.get("panel_footer"))
    img = (s.get("panel_image_url") or "").strip()
    if img.startswith("http"):
        em.set_image(url=img)
    return em
