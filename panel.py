import discord
import store

COLOR = 0x5865F2

async def build_panel():
    s = store.load_settings()
    try:
        color = int(s.get("panel_color", COLOR))
    except Exception:
        color = COLOR
    em = discord.Embed(title=s.get("panel_title", "Ticket"),
                       description=s.get("panel_description", ""),
                       color=color)
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
