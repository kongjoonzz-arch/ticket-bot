import asyncio
import discord
import store
import ticket_utils as tu
from ui_complete import _find_ticket


async def do_complete_ticket(guild, channel, admin_user):
    """구매완료: 역할 지급 + 구매 카드 + 구매로그 + 후기 DM."""
    from ui_review import send_review_dm
    from ui_close import ClosedTicketView
    from ui_receipt import send_purchase_receipt, new_purchase_id, send_log_with_card

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
    # 대시보드에서 상품 정보가 수정됐다면 최신 값으로 맞춘다 (삭제된 상품이면 예전 스냅샷 유지)
    pid = str(product.get("id") or "").strip()
    if pid:
        cur = next((p for p in store.load_products() if str(p.get("id")) == pid), None)
        if isinstance(cur, dict):
            merged = dict(product)
            for k in ("name", "category", "price", "quantity", "discount", "stock"):
                if k in cur:
                    merged[k] = cur[k]
            product = merged
            t["product"] = product
    try:
        price = f"{int(product.get('price', 0)):,}원"
    except Exception:
        price = str(product.get("price", ""))

    # 구매자 역할 지급 (실패 원인을 바로 알 수 있게 안내)
    role_txt = "- (설정 안 됨)"
    rid = str(s.get("buyer_role_id") or "").strip()
    if rid and not rid.isdigit():
        role_txt = "❌ buyer_role_id 값이 숫자(ID)가 아닙니다"
    elif rid.isdigit():
        role = guild.get_role(int(rid))
        me = getattr(guild, "me", None)
        if role is None:
            role_txt = "❌ 역할을 찾을 수 없음 (역할 ID 확인 / 봇이 서버에 있는지 확인)"
        elif member is None:
            role_txt = "❌ 대상 멤버를 찾을 수 없음 (서버를 떠난 사용자)"
        elif me is None:
            role_txt = "❌ 봇 멤버 정보를 가져올 수 없음"
        elif not getattr(me.guild_permissions, "manage_roles", False):
            role_txt = "❌ 봇에 '역할 관리' 권한이 없습니다 (서버 설정 → 역할 → 봇 권한 ON)"
        elif getattr(role, "managed", False):
            role_txt = "❌ 다른 앱/부스트가 관리하는 역할은 지급할 수 없습니다"
        elif role.position >= getattr(getattr(me, "top_role", None), "position", 0):
            role_txt = "❌ 봇의 최상위 역할이 대상 역할보다 낮습니다 (봇 역할을 위로 올려주세요)"
        else:
            try:
                await member.add_roles(role, reason=f"ticket #{t.get('no')} 구매완료")
                role_txt = role.mention
            except discord.Forbidden:
                role_txt = "❌ 권한 부족(403) · 봇 역할을 대상 역할보다 위로 올려주세요"
            except discord.HTTPException as e:
                role_txt = f"❌ 지급 실패 (HTTP {getattr(e, 'status', '?')})"
            except Exception as e:
                role_txt = f"❌ 지급 실패: {e}"

    # 티켓 상태 + 구매 ID 저장
    rec = None
    tickets = store.load_tickets()
    for x in tickets:
        if x.get("channel_id") == channel.id:
            x["status"] = "completed"
            x["completed_at"] = tu.now_kst_str()
            x["completed_by"] = str(admin_user)
            x["purchase_id"] = str(x.get("purchase_id") or "") or new_purchase_id()
            x["product"] = product
            rec = x

    # 구매완료 시 재고 차감
    stock_note = ""
    try:
        qty = max(1, int(product.get("quantity", 1) or 1))
    except Exception:
        qty = 1
    stock_on = s.get("stock_enabled", True)
    if isinstance(stock_on, str):
        stock_on = stock_on.strip().lower() == "true"
    if stock_on and pid:
        changed, left = store.adjust_stock(pid, -qty)
        if changed:
            product = dict(product)
            product["stock"] = left
            if rec is not None:
                rec["product"] = product
            stock_note = f"{left}개 남음" + (" · ⚠️ 품절" if left == 0 else "")
    store.save_tickets(tickets)
    if rec is None:
        rec = dict(t)
        rec["purchase_id"] = str(rec.get("purchase_id") or "") or new_purchase_id()

    keep = bool(s.get("close_keep_channel", True))
    delete_label = str(s.get("delete_button_label") or "🗑️ 채널 삭제")[:80]
    view = None
    delete_btn = None
    if keep:
        view = ClosedTicketView(delete_label)
        delete_btn = {"type": 2, "style": 4, "label": delete_label, "custom_id": "ticket:delete"}

    # 구매 완료 카드
    _sent, ctx = await send_purchase_receipt(channel, rec, member, view=view, delete_button=delete_btn)

    if keep:
        if member is not None:
            try:
                await channel.set_permissions(member, view_channel=True, read_message_history=True,
                                              send_messages=False, attach_files=False,
                                              add_reactions=False, reason="구매완료 - 읽기 전용")
            except Exception as e:
                print(f"[complete] read-only failed: {e}")
    else:
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

    # 구매 로그
    log = tu.apex_embed(s, str(s.get("complete_log_title") or "✅ 구매완료"),
                        f"🏷️ {ctx['category']} · **{ctx['product']}**", color=0x57F287)
    log.add_field(name="구매자", value=(member.mention if member else str(t.get("user_name"))), inline=True)
    log.add_field(name="담당", value=admin_user.mention, inline=True)
    log.add_field(name="갯수 / 할인", value=f"{ctx['quantity']}개 / {ctx['discount_txt']}", inline=True)
    log.add_field(name="결제금액", value=f"**{ctx['total_txt']}**", inline=True)
    log.add_field(name="지급 역할", value=role_txt, inline=True)
    log.add_field(name="단가", value=price, inline=True)
    if stock_note:
        log.add_field(name="재고", value=stock_note, inline=True)
    log.add_field(name="구매 ID", value=f"`{ctx['purchase_id']}`", inline=False)
    log.add_field(name="채널", value=channel.mention, inline=False)
    if not await send_log_with_card(guild, s, ctx.get("image"), log):
        await tu.send_purchase_log(guild, s, log)

    # 후기 DM (상품명 포함)
    if member is not None:
        await send_review_dm(guild, member, t.get("no"), ctx["product"], category=ctx["category"])

    return True, (f"구매완료 · {ctx['category']} · {ctx['product']} · {ctx['total_txt']}\n"
                  f"역할: {'지급 완료 · ' + role_txt if role_txt.startswith('<@&') else role_txt}\n"
                  f"후기 DM: {'발송 완료' if member is not None else '대상 없음(발송 불가)'}"
                  + (f"\n재고: {stock_note}" if stock_note else ""))
