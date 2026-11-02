# -*- coding: utf-8 -*-
"""/상품지급 — 상품 내용을 DM 카드로 전달 (긴 텍스트/줄바꿈 안전 처리)."""
import io
import re
import discord
import store
import ticket_utils as tu
from ui_receipt import send_v2

MAX_TEXT = 3500


def normalize_text(text):
    """\\r\\n -> \\n 정규화 + 앞뒤 공백 정리 (줄바꿈은 그대로 유지)."""
    if text is None:
        return ""
    t = str(text).replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\u200b", "").replace("\ufeff", "")
    return t.strip("\n")


def split_lines(text, limit=MAX_TEXT):
    """줄바꿈을 깨지 않고 limit 이하 조각으로 분할 (한 줄이 너무 길 때만 강제 분할)."""
    text = normalize_text(text)
    if not text:
        return [""]
    parts, cur = [], ""
    for line in text.split("\n"):
        while len(line) > limit:
            if cur:
                parts.append(cur)
                cur = ""
            parts.append(line[:limit])
            line = line[limit:]
        candidate = (cur + "\n" + line) if cur else line
        if len(candidate) > limit:
            parts.append(cur)
            cur = line
        else:
            cur = candidate
    if cur:
        parts.append(cur)
    return parts or [""]


def is_long(text, limit=MAX_TEXT):
    return len(normalize_text(text)) > limit


def safe_filename(name, default="product"):
    t = re.sub(r'[\\/:*?"<>|\n\r\t]+', "_", str(name or "")).strip(" ._")
    return (t or default)[:60]


def _color(settings=None):
    try:
        return int((settings or {}).get("panel_color", 0x5865F2))
    except Exception:
        return 0x5865F2


def gift_context(user, product, content, admin_name="관리자", note=""):
    content = normalize_text(content)
    product = (str(product or "").strip() or "상품")
    receiver = ""
    try:
        receiver = str(getattr(user, "display_name", None) or getattr(user, "name", "") or "")
    except Exception:
        receiver = ""
    receiver = receiver or str(user) or "고객"
    head = split_lines(content, MAX_TEXT)[0] if content else "지급된 내용이 없습니다."
    foot = f"지급: {admin_name} · {tu.now_kst_str()} (KST)"
    if note:
        foot += f" · {note}"
    return {
        "product": product,
        "subtitle": "상품이 지급되었습니다 🎉",
        "receiver": receiver,
        "content": head,
        "footer": foot,
        "long": is_long(content),
        "full": content,
    }


def build_gift_v2(ctx, settings):
    try:
        comps = [
            {"type": 10, "content": f"# 🎁 {ctx['product']}\n{ctx['subtitle']}"},
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": f"**받는 사람**\n{ctx['receiver']}"},
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": ctx["content"] or "-"},
            {"type": 14, "divider": True, "spacing": 1},
            {"type": 10, "content": f"-# {ctx['footer']}"},
        ]
        return {"flags": 32768,
                "components": [{"type": 17, "accent_color": _color(settings),
                                "components": comps}]}
    except Exception as e:
        print(f"[gift] v2 build failed: {e}")
        return None


def build_gift_embed(ctx, settings, with_file_notice=False):
    em = discord.Embed(title=f"🎁 {ctx['product']}", description=ctx["content"] or "-",
                       color=_color(settings))
    em.add_field(name="받는 사람", value=ctx["receiver"], inline=False)
    if with_file_notice:
        em.add_field(name="📎 전체 내용",
                     value="아래 **txt 파일**에서 전체 내용을 확인해주세요. (줄바꿈 그대로 저장됨)",
                     inline=False)
    em.set_footer(text=ctx["footer"])
    return em


async def _get_dm(user):
    dm = getattr(user, "dm_channel", None)
    if dm is not None:
        return dm
    try:
        return await user.create_dm()
    except Exception as e:
        print(f"[gift] dm open failed: {e}")
        return None


async def send_product_dm(user, product, content, admin_name="관리자"):
    """상품 내용을 DM 카드로 전송. (성공여부, 결과메시지) 반환."""
    s = store.load_settings()
    ctx = gift_context(user, product, content, admin_name=admin_name)
    dm = await _get_dm(user)
    if dm is None:
        return False, "DM 채널을 열 수 없어요 (상대가 DM 차단 / 서버 밖 사용자)"
    if not ctx["long"]:
        payload = build_gift_v2(ctx, s)
        if payload is not None:
            sent = await send_v2(dm, payload)
            if sent is not None:
                return True, "DM 카드 전송 완료"
        try:
            await dm.send(embed=build_gift_embed(ctx, s))
            return True, "DM 전송 완료 (임베드)"
        except discord.Forbidden:
            return False, "DM 차단됨 (상대가 DM을 막았거나 서버 밖 사용자)"
        except Exception as e:
            return False, f"DM 전송 실패: {e}"
    # 긴 내용: 카드 미리보기 + 전체 내용 txt 첨부 (줄바꿈 그대로)
    buf = io.BytesIO(ctx["full"].encode("utf-8"))
    fname = f"{safe_filename(ctx['product'])}.txt"
    try:
        await dm.send(embed=build_gift_embed(ctx, s, with_file_notice=True),
                      file=discord.File(buf, filename=fname))
        return True, f"DM 전송 완료 (긴 내용 {len(ctx['full']):,}자 · {fname} 첨부)"
    except discord.Forbidden:
        return False, "DM 차단됨 (상대가 DM을 막았거나 서버 밖 사용자)"
    except Exception as e:
        return False, f"DM 전송 실패: {e}"


async def log_gift(guild, settings, admin, member, product, content_len, ok, result):
    s = settings or store.load_settings()
    em = tu.apex_embed(s, "🎁 상품 지급" if ok else "⚠️ 상품 지급 실패",
                       f"**{str(product or '상품')}** · {int(content_len):,}자",
                       color=0x57F287 if ok else 0xED4245)
    em.add_field(name="받는 사람", value=str(getattr(member, "mention", member)), inline=True)
    em.add_field(name="담당", value=str(getattr(admin, "mention", admin)), inline=True)
    em.add_field(name="결과", value=str(result)[:500], inline=False)
    try:
        await tu.send_purchase_log(guild, s, em)
    except Exception as e:
        print(f"[gift] log failed: {e}")


class ProductGiveModal(discord.ui.Modal):
    """상품명 + 지급 내용(줄바꿈 가능)을 입력받아 DM으로 전송."""

    def __init__(self, member, product=""):
        super().__init__(title="상품 지급")
        self.member = member
        self.product = str(product or "")
        self.add_item(discord.ui.TextInput(
            label="상품 이름", default=self.product[:100], required=False,
            placeholder="예: 기부쿠키 울트라", max_length=100,
            style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(
            label="지급 내용 (줄바꿈 가능)", required=True, max_length=4000,
            placeholder="계정 정보 / 쿠폰번호 / 안내문 등",
            style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        product = (self.children[0].value or "").strip() or self.product or "상품"
        content = self.children[1].value or ""
        ok, msg = await send_product_dm(self.member, product, content,
                                        admin_name=str(interaction.user))
        try:
            await log_gift(interaction.guild, store.load_settings(), interaction.user,
                           self.member, product, len(normalize_text(content)), ok, msg)
        except Exception:
            pass
        if ok:
            em = tu.ok_embed("🎁 상품 지급 완료",
                             f"{getattr(self.member, 'mention', self.member)} 님에게 DM을 보냈습니다.\n> {msg}",
                             color=0x57F287)
        else:
            em = tu.err_embed(f"상품 지급 실패\n{msg}")
        try:
            await interaction.followup.send(embed=em, ephemeral=True)
        except Exception:
            pass
