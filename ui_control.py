import discord
import store
import ticket_utils as tu

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _guard_admin(self, interaction):
        s = store.load_settings()
        if tu.is_admin(interaction.user, s):
            return True
        await interaction.response.send_message("Admin only.", ephemeral=True)
        return False

    def _find(self, ch_id):
        for t in store.load_tickets():
            if t.get("channel_id") == ch_id:
                return t
        return None

    @discord.ui.button(label="Confirm", emoji="✅", style=discord.ButtonStyle.success, custom_id="ticket:confirm")
    async def confirm_btn(self, interaction, button):
        if not await self._guard_admin(interaction):
            return
        t = self._find(interaction.channel_id)
        st = f" (status: {t.get('status')})" if t else ""
        await interaction.response.send_message(f"Purchase confirmed by admin.{st}")

    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket:close")
    async def close_btn(self, interaction, button):
        if not await self._guard_admin(interaction):
            return
        from ui_close import CloseReasonModal
        await interaction.response.send_modal(CloseReasonModal())
