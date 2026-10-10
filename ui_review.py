import discord
import store
import ticket_utils as tu


async def _save_pending(user_id, ticket_no, stars, guild_id):
    try:
        import json as _j
        import os as _o
        pp = _o.path.join(store.DATA_DIR, "review_pending.json")
        cur = {}
        if _o.path.exists(pp):
            with open(pp, "r", encoding="utf-8") as f:
                cur = _j.load(f)
        cur[str(user_id)] = {"ticket_no": ticket_no, "stars": stars, "guild_id": guild_id}
        with open(pp, "w", encoding="utf-8") as f:
            _j.dump(cur, f, ensure_ascii=False, indent=2)
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
        if not ticket_no:
            try:
                import json as _j
                import os as _o
                pp = _o.path.join(store.DATA_DIR, "review_pending.json")
                if _o.path.exists(pp):
                    with open(pp, "r", encoding="utf-8") as f:
                        cur = _j.load(f)
                    info = cur.get(str(interaction.user.id), {})
                    ticket_no = info.get("ticket_no", 0)
                    guild_id = info.get("guild_id", guild_id)
            except Exception:
                pass
        if not guild_id:
            try:
                guild_id = interaction.guild.id if interaction.guild else 0
            except Exception:
                guild_id = 0
        await _save_pending(interaction.user.id, ticket_no, stars, guild_id)
        s = store.load_settings()
        need = int(s.get("review_min_length", 5) or 5)
        em = tu.ok_embed("⭐ 별점 접수", f"**{stars}점** 접수됐어요!\n이제 이 DM에 후기를 **{need}자 이상** 적어주세요 🙂", color=0xFEE75C)
        try:
            await interaction.followup.send(embed=em, ephemeral=True)
        except Exception:
            pass


async def send_review_dm(guild, member, ticket_no, product_name):
    s = store.load_settings()
    mapping = {"no": ticket_no, "user_mention": member.mention, "product": product_name or "상품"}
    title = tu.fill(s.get("review_dm_title", ""), mapping).replace("#{no}", f"#{ticket_no}")
    msg = tu.fill(s.get("review_dm_message", ""), mapping).replace("#{no}", f"#{ticket_no}")
    thumb = None
    try:
        thumb = guild.icon.url if getattr(guild, "icon", None) else None
    except Exception:
        thumb = None
    try:
        await member.send(embed=tu.apex_embed(s, title, msg))
    except Exception:
        pass
    await _save_pending(member.id, ticket_no, 5, guild.id)
    try:
        await member.send(view=ReviewStarsView(ticket_no, guild.id),
                          embed=tu.ok_embed("⭐ 별점 선택", "별점을 눌러주세요. (DM 전용)", color=0xFEE75C))
    except Exception as e:
        print(f"[review] dm failed: {e}")
        return False
    return True
