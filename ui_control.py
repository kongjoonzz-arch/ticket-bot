import discord
import store
import ticket_utils as tu

DIV = "━━━━━━━━━━━━━━━"

class TicketControlView(discord.ui.View):
    def __init__(self, close_label="🔒 티켓 닫기", complete_label="✅ 구매완료"):
        super().__init__(timeout=None)
        self.close_btn.label = str(close_label or "🔒 티켓 닫기")[:80]
        self.complete_btn.label = str(complete_label or "✅ 구매완료")[:80]

    async def _guard_admin(self, interaction):
        s = store.load_settings()
        if tu.is_admin(interaction.user, s):
            return True
        await interaction.response.send_message(embed=tu.err_embed("이 버튼은 **관리자만** 사용할 수 있어요."), ephemeral=True)
        return False

    @discord.ui.button(label="✅ 구매완료", style=discord.ButtonStyle.success, custom_id="ticket:complete")
    async def complete_btn(self, interaction, button):
        if not await self._guard_admin(interaction):
            return
        from ui_done import do_complete_ticket
        await interaction.response.defer(ephemeral=True, thinking=False)
        ok, msg = await do_complete_ticket(interaction.guild, interaction.channel, interaction.user)
        em = tu.ok_embed("✅ 구매완료", msg, color=0x57F287) if ok else tu.err_embed(msg)
        try:
            await interaction.followup.send(embed=em, ephemeral=True)
        except Exception:
            pass

    @discord.ui.button(label="🔒 티켓 닫기", style=discord.ButtonStyle.danger, custom_id="ticket:close")
    async def close_btn(self, interaction, button):
        if not await self._guard_admin(interaction):
            return
        from ui_close import CloseReasonModal
        await interaction.response.send_modal(CloseReasonModal())
