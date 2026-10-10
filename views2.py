# -*- coding: utf-8 -*-
# UNUSED legacy file - safe to delete. (ui_modal.py 사용)

import discord
import store
import ticket_utils as tu


class QuestionModal(discord.ui.Modal):
    def __init__(self, kind, product=None):
        qs = store.load_questions()
        qlist = [q for q in qs.get(kind, []) if q.get("enabled", True)][:5]
        title = "Buy Ticket" if kind == "buy" else "Error Ticket"
        super().__init__(title=title)
        self.kind = kind
        self.product = product
        self.qlist = qlist
        for q in qlist:
            label = str(q.get("label", "Q"))[:45]
            ph = str(q.get("placeholder", ""))[:100] or None
            req = bool(q.get("required", True))
            ml = int(q.get("max_length", 200) or 200)
            style = discord.TextStyle.paragraph if ml > 100 else discord.TextStyle.short
            self.add_item(discord.ui.TextInput(label=label, placeholder=ph,
                                               required=req, max_length=ml,
                                               style=style))
