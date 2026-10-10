import asyncio
import discord
import store
import ticket_utils as tu
from ui_complete import _find_ticket, DIV


async def do_complete_ticket(guild, channel, admin_user):
    from ui_review import send_review_dm
    s = store.load_settings()
    t = _find_ticket(channel.id)
    if t is None:
        return False, "이 채널은 티켓이 아니에요."
    if t.get("status") == "completed":
        return False, "이미 구매완료 처리된 티켓이에요."
    if t.get("kind") != "buy":
        return False, "구매 문의 티켓에서만 구매완료를 할 수 있어요."
    member = None
    try:
        member = guild.get_member(int(t.get("user_id"))) or await guild.fetch_member(int(t.get("user_id")))
    except Exception:
        member = None
    product = t.get("product") or {}
    pname = product.get("name", "상품")
    try:
        price = f"{int(product.get('price', 0)):,}원"
    except Exception:
        price = str(product.get("price", ""))
    role_txt = "-"
    rid = str(s.get("buyer_role_id") or "").strip()
    if member is not None and rid.isdigit():
        role = guild.get_role(int(rid))
        if role is not None:
            try:
                await member.add_roles(role, reason=f"ticket #{t.get('no')} 구매완료")
                role_txt = role.mention
            except Exception as e:
                role_txt = f"역할 지급 실패: {e}"
        else:
            role_txt = "역할 ID를 확인해주세요."
    tickets = store.load_tickets()
    for x in tickets:
        if x.get("channel_id") == channel.id:
            x["status"] = "completed"
            x["completed_at"] = tu.now_kst_str()
            x["completed_by"] = str(admin_user)
    store.save_tickets(tickets)
    em = tu.apex_embed(s, str(s.get("complete_title") or "✅ 구매완료 처리"), color=0x57F287)
    em.description = f"{DIV()}\n{tu.fill(str(s.get('complete_message') or ''), {'user_mention': member.mention if member else '', 'no': t.get('no'), 'product': pname})}\n{DIV()}"
    em.add_field(name="🎁 상품", value=f"**{pname}** · {price}", inline=False)
    em.add_field(name="👤 구매자", value=(member.mention if member else str(t.get("user_name"))), inline=True)
    em.add_field(name="🏷️ 지급 역할", value=role_txt, inline=True)
    try:
        await channel.send(embed=em)
    except Exception:
        pass
    log = tu.apex_embed(s, str(s.get("complete_log_title") or "✅ 구매완료"), f"티켓 #{t.get('no')} · {pname} · {price}", color=0x57F287)
    log.add_field(name="구매자", value=(member.mention if member else str(t.get("user_name"))), inline=True)
    log.add_field(name="담당", value=admin_user.mention, inline=True)
    log.add_field(name="채널", value=channel.mention, inline=False)
    await tu.send_purchase_log(guild, s, log)
    if member is not None:
        await send_review_dm(guild, member, t.get("no"), pname)
    try:
        delay = int(s.get("delete_delay_sec", 5) or 5)
    except Exception:
        delay = 5
    if bool(s.get("delete_on_close", True)):
        await asyncio.sleep(max(1, min(delay, 30)))
        try:
            await channel.delete(reason=f"ticket #{t.get('no')} completed")
        except Exception as e:
            print(f"[complete] delete failed: {e}")
    return True, f"티켓 #{t.get('no')} 구매완료 · {pname} · 역할 지급 + 후기 DM 발송"
