# -*- coding: utf-8 -*-
"""별점 선택 + 후기 DM 흐름 (상품명 포함)."""
import json
import os
import discord
import store
import ticket_utils as tu


def _pending_path():
    return os.path.join(store.DATA_DIR, "review_pending.json")


def _load_all_pending():
    pp = _pending_path()
    if not os.path.exists(pp):
        return {}
    try:
        with open(pp, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _load_pending(user_id):
    return _load_all_pending().get(str(user_id), {}) or {}


async def _save_pending(user_id, ticket_no, stars, guild_id, product="", category=""):
    try:
        cur = _load_all_pending()
        cur[str(user_id)] = {
            "ticket_no": ticket_no,
            "stars": stars,
            "guild_id": guild_id,
            "product": str(product or ""),
            "category": str(category or ""),
            "at": tu.now_kst_str(),
        }
        with open(_pending_path(), "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[review] pending save failed: {e}")


class ReviewStarsView(discord.ui.View):
    def __init__(self, ticket_no=0, guild_id=0):
        super().__init__(timeout=None)
        self._ticket_no = ticket_no
        self._guild_id = guild_id

    @discord.ui.button(label="5점", emoji="⭐", style=discord.ButtonStyle.primary, custom_id="review:5")
    async def s5(self, interaction, button):
        await self._save(interaction, 5)

    @discord.ui.button(label="4점", emoji="⭐", style=discord.ButtonStyle.secondary, custom_id="review:4")
    async def s4(self, interaction, button):
        await self._save(interaction, 4)

    @discord.ui.button(label="3점", emoji="⭐", style=discord.ButtonStyle.secondary, custom_id="review:3")
    async def _s3(self, interaction, button):
        await self._save(interaction, 3)

    @discord.ui.button(label="2점", emoji="⭐", style=discord.ButtonStyle.secondary, custom_id="review:2")
    async def _s2(self, interaction, button):
        await self._save(interaction, 2)

    @discord.ui.button(label="1점", emoji="⭐", style=discord.ButtonStyle.secondary, custom_id="review:1")
    async def _s1(self, interaction, button):
        await self._save(interaction, 1)

    async def _save(self, interaction, stars):
        await interaction.response.defer(ephemeral=True, thinking=False)
        ticket_no = self._ticket_no or 0
        guild_id = self._guild_id or 0
        try:
            cid = str((interaction.data or {}).get("custom_id", ""))
            parts = cid.split(":")
            if len(parts) >= 2:
                stars = int(parts[-1])
        except Exception:
            pass
        info = _load_pending(interaction.user.id)
        if not ticket_no:
            ticket_no = info.get("ticket_no", 0)
        if not guild_id:
            try:
                guild_id = info.get("guild_id", 0) or (interaction.guild.id if interaction.guild else 0)
            except Exception:
                guild_id = 0
        await _save_pending(interaction.user.id, ticket_no, stars, guild_id,
                            product=info.get("product", ""), category=info.get("category", ""))
        s = store.load_settings()
        need = int(s.get("review_min_length", 5) or 5)
        product = str(info.get("product") or "").strip()
        extra = f"\n🛍️ 상품: **{product}**" if product else ""
        em = tu.ok_embed("⭐ 별점 접수",
                         f"**{stars}점** 접수됐어요!{extra}\n이제 이 DM에 후기를 **{need}자 이상** 적어주세요 🙂",
                         color=0xFEE75C)
        try:
            await interaction.followup.send(embed=em, ephemeral=True)
        except Exception:
            pass


async def send_review_dm(guild, member, ticket_no, product_name, category=""):
    """구매완료 후 후기 요청 DM (상품명/카테고리 포함)."""
    s = store.load_settings()
    product_name = str(product_name or "상품")
    category = str(category or "").strip() or "기타"
    mapping = {"no": ticket_no, "user_mention": member.mention,
               "product": product_name, "category": category}
    title = tu.fill(s.get("review_dm_title", ""), mapping).replace("#{no}", f"#{ticket_no}")
    msg = tu.fill(s.get("review_dm_message", ""), mapping).replace("#{no}", f"#{ticket_no}")
    try:
        em = tu.apex_embed(s, title, msg)
        em.add_field(name="🛍️ 상품",
                     value=f"**{product_name}**\n🏷️ {category}",
                     inline=False)
        await member.send(embed=em)
    except Exception as e:
        print(f"[review] dm failed: {e}")
        return False
    await _save_pending(member.id, ticket_no, 5, guild.id, product=product_name, category=category)
    try:
        await member.send(view=ReviewStarsView(ticket_no, guild.id),
                          embed=tu.ok_embed("⭐ 별점 선택",
                                            f"**{product_name}** 은 어떠셨나요?\n아래 별점을 눌러주세요. (DM 전용)",
                                            color=0xFEE75C))
    except Exception as e:
        print(f"[review] dm failed: {e}")
        return False
    return True
