# -*- coding: utf-8 -*-
"""Purchase complete shared logic."""
import store
import ticket_utils as tu


def _find_ticket(channel_id):
    for t in store.load_tickets():
        if t.get("channel_id") == channel_id:
            return t
    return None


def DIV():
    return "━━━━━━━━━━━━━━━"


