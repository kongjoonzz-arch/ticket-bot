# -*- coding: utf-8 -*-
"""JSON 파일 기반 저장소 (상품/질문/패널문구/티켓)."""
import copy
import json
import os
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
TICKETS_FILE = os.path.join(DATA_DIR, "tickets.json")
COMMANDS_FILE = os.path.join(DATA_DIR, "commands.json")
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.json")

_lock = threading.Lock()

# 서버 기본 ID (설정값이 비어 있으면 자동 적용 · 값을 'none' 으로 두면 비활성)
DEFAULT_IDS = {
    "ticket_category_id": "1538518399066308668",
    "buy_category_id": "1538518399066308668",
    "error_category_id": "1538518399066308668",
    "ticket_log_channel_id": "1538072438691332177",
    "purchase_log_channel_id": "1537817248457170964",
    "review_channel_id": "1537817307475349554",
    "buyer_role_id": "1538126406662225981",
}

DEFAULT_SETTINGS = {
    "panel_title": "🎫 PREMIUM SUPPORT",
    "panel_description": "원하시는 문의를 선택해주세요.\n\n🛒 구매 문의 — 상품 구매·입금 안내\n❓ 오류 문의 — 입금 오류·상품 문제 해결",
    "panel_button_buy": "구매 문의",
    "panel_button_error": "오류 문의",
    "panel_button_buy_emoji": "",
    "panel_button_error_emoji": "",
    "panel_footer": "24시간 운영 · 평균 응답 10분 이내",
    "panel_image_url": "",
    "panel_thumbnail_url": "",
    "panel_color": 5814783,
    **DEFAULT_IDS,
    "one_ticket_per_user": True,
    "complete_button_label": "✅ 구매완료",
    "complete_title": "✅ 구매완료 처리",
    "complete_message": "구매가 완료되었습니다. 이용해 주셔서 감사합니다!",
    "complete_log_title": "✅ 구매완료",
    "review_dm_title": "⭐ 후기를 남겨주세요!",
    "review_dm_message": "안녕하세요 {user_mention}님!\n**{product}** 구매가 완료되었습니다 🎉\n\n아래에서 별점을 골라주세요. 그 다음 DM으로 후기를 적어주시면 후기 채널에 자동 등록됩니다.",
    "review_title_format": "⭐ {stars} · {user}",
    "review_min_length": 5,
    "admin_role_id": "",
    "mention_admin_on_create": True,
    "mention_text": "📢 관리자님, 새 티켓이 열렸습니다! {admin_mention} 확인 부탁드립니다.",
    "welcome_message": "안녕하세요 {user_mention}님! 문의 내용을 정리해드렸어요.\n관리자가 곧 확인해드립니다. 추가 설명이 있으면 이 채널에 적어주세요 🙂",
    "close_message": "🔒 티켓이 닫혔습니다. 이용해 주셔서 감사합니다!",
    "close_keep_channel": True,
    "delete_button_label": "🗑️ 채널 삭제",
    "delete_on_close": False,
    "delete_delay_sec": 3,
    "ticket_button_label": "🔒 티켓 닫기",
    "purchase_card_title": "구매 완료",
    "purchase_card_message": "구매가 정상적으로 완료되었습니다",
    "card_image_enabled": True,
    "stock_enabled": True,
    "stock_log_channel_id": "",
    "receipt_brand": "",
    "card_accent": "",
    "dm_on_open": True,
    "dm_open_title": "🎫 티켓이 열렸습니다!",
    "dm_open_message": "안녕하세요 {user_mention}님!\n{kind} 티켓이 열렸습니다.\n{channel} 에서 대화를 이어가주세요.\n\n{product}\n\n{answers}",
    "dm_on_close": True,
    "dm_close_title": "🔒 티켓이 닫혔습니다.",
    "dm_close_message": "안녕하세요 {user_mention}님!\n{kind} 티켓이 닫혔습니다.\n\n📌 닫기 사유: {reason}\n\n추가 문의가 있으면 새 티켓을 열어주세요 🙂",
    "close_reason_placeholder": "예: 입금 확인 완료 / 상품 전달 완료 / 중복 티켓 정리",
    "close_reason_required": False,
    "announce_channel_id": "",
    "announce_title": "📢 공지사항",
    "announce_message": "여기에 공지 내용을 입력하세요.",
    "announce_color": 5814783,
    "announce_image_url": "",
    "announce_footer": "",
    "announce_mention": "none",
    "announce_mention_role_id": "",
    "keepalive_enabled": True,
    "keepalive_url": "",
}
NOTICES_FILE = os.path.join(DATA_DIR, "notices.json")
REVIEWS_FILE = os.path.join(DATA_DIR, "reviews.json")

DEFAULT_QUESTIONS_BUY = [
    {"id": "q1", "label": "입금자명", "placeholder": "예: 홍길동", "required": True, "max_length": 50, "enabled": True},
    {"id": "q2", "label": "연락처 / 메신저 ID", "placeholder": "예: 010-0000-0000 또는 디스코드 ID", "required": True, "max_length": 100, "enabled": True},
    {"id": "q3", "label": "요청사항", "placeholder": "추가로 남기실 말 (없으면 '없음')", "required": False, "max_length": 300, "enabled": True},
]

DEFAULT_QUESTIONS_ERROR = [
    {"id": "e1", "label": "문제 종류", "placeholder": "예: 입금했는데 상품이 안 왔어요", "required": True, "max_length": 100, "enabled": True},
    {"id": "e2", "label": "입금자명 / 주문정보", "placeholder": "예: 홍길동 / 구매한 상품명", "required": True, "max_length": 100, "enabled": True},
    {"id": "e3", "label": "상세 설명", "placeholder": "언제, 무엇을, 어떻게 되었는지 자세히 적어주세요", "required": True, "max_length": 500, "enabled": True},
]

# ---------------------------------------------------------------------------
# 기본 카테고리 / 기본 상품 (로블록스 쿠키 가격표)
# data 파일이 없거나 비어 있으면(초기화/재배포) 이 값으로 자동 복구됩니다.
# ---------------------------------------------------------------------------
DEFAULT_CATEGORIES = ["기본 쿠키", "프리미엄 쿠키", "로벅스 사용 쿠키", "로벅스 충전 쿠키"]

DEFAULT_PRODUCTS = [
    {"id": "c01", "name": "로블랜덤쿠키", "category": "기본 쿠키", "price": 600,
     "quantity": 1, "discount": 0, "stock": 100, "order": 1,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c02", "name": "입양쿠키", "category": "기본 쿠키", "price": 1100,
     "quantity": 1, "discount": 0, "stock": 100, "order": 2,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c03", "name": "블레이드볼쿠키", "category": "기본 쿠키", "price": 1400,
     "quantity": 1, "discount": 0, "stock": 100, "order": 3,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c04", "name": "블록스피스쿠키", "category": "기본 쿠키", "price": 1500,
     "quantity": 1, "discount": 0, "stock": 100, "order": 4,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c05", "name": "브홀쿠키", "category": "기본 쿠키", "price": 1600,
     "quantity": 1, "discount": 0, "stock": 100, "order": 5,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c06", "name": "리미티드쿠키", "category": "기본 쿠키", "price": 2200,
     "quantity": 1, "discount": 0, "stock": 100, "order": 6,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c07", "name": "랜덤로벅쿠키", "category": "기본 쿠키", "price": 2200,
     "quantity": 1, "discount": 0, "stock": 100, "order": 7,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c08", "name": "벌시물쿠키", "category": "기본 쿠키", "price": 2800,
     "quantity": 1, "discount": 0, "stock": 100, "order": 8,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c09", "name": "배구전설쿠키", "category": "프리미엄 쿠키", "price": 3200,
     "quantity": 1, "discount": 0, "stock": 100, "order": 9,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c10", "name": "입양갭때쿠키", "category": "프리미엄 쿠키", "price": 3300,
     "quantity": 1, "discount": 0, "stock": 100, "order": 10,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c11", "name": "머더미스테리 갭때쿠키", "category": "프리미엄 쿠키", "price": 3500,
     "quantity": 1, "discount": 0, "stock": 100, "order": 11,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c12", "name": "1만로벅이상사용 쿠키", "category": "로벅스 사용 쿠키", "price": 2400,
     "quantity": 1, "discount": 0, "stock": 100, "order": 12,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c13", "name": "3만로벅이상사용 쿠키", "category": "로벅스 사용 쿠키", "price": 4500,
     "quantity": 1, "discount": 0, "stock": 100, "order": 13,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c14", "name": "5만로벅이상사용 쿠키", "category": "로벅스 사용 쿠키", "price": 5500,
     "quantity": 1, "discount": 0, "stock": 100, "order": 14,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c15", "name": "50로벅 이상 쿠키", "category": "로벅스 충전 쿠키", "price": 3000,
     "quantity": 1, "discount": 0, "stock": 100, "order": 15,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c16", "name": "100로벅 이상 쿠키", "category": "로벅스 충전 쿠키", "price": 5000,
     "quantity": 1, "discount": 0, "stock": 100, "order": 16,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c17", "name": "200로벅 이상 쿠키", "category": "로벅스 충전 쿠키", "price": 10000,
     "quantity": 1, "discount": 0, "stock": 100, "order": 17,
     "description": "로블록스 쿠키", "enabled": True},
    {"id": "c18", "name": "500로벅 이상 쿠키", "category": "로벅스 충전 쿠키", "price": 20000,
     "quantity": 1, "discount": 0, "stock": 100, "order": 18,
     "description": "로블록스 쿠키", "enabled": True},
]



def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _read_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[store] {path} 로드 실패: {e}")
    return copy.deepcopy(default)


def _write_json(path, data):
    _ensure_dir()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_products():
    with _lock:
        return _read_json(PRODUCTS_FILE, [])


def save_products(products):
    with _lock:
        _write_json(PRODUCTS_FILE, products)


def load_category_order():
    """카테고리 표시 순서. 저장된 값이 비어 있으면 기본 카테고리로 복구."""
    with _lock:
        data = _read_json(CATEGORIES_FILE, {"order": list(DEFAULT_CATEGORIES)})
    raw = data.get("order") if isinstance(data, dict) else data
    out = []
    for c in (raw or []):
        c = str(c or "").strip()
        if c and c not in out:
            out.append(c)
    return out or list(DEFAULT_CATEGORIES)


def save_category_order(order):
    arr = []
    for c in (order or []):
        c = str(c or "").strip()
        if c and c not in arr:
            arr.append(c)
    with _lock:
        _write_json(CATEGORIES_FILE, {"order": arr})
    return arr


def ensure_defaults():
    """상품/카테고리 파일이 없거나 비어 있으면 기본값으로 복구 (초기화/재배포 대비)."""
    _ensure_dir()
    try:
        existing = _read_json(PRODUCTS_FILE, [])
    except Exception:
        existing = []
    if not isinstance(existing, list) or not existing:
        _write_json(PRODUCTS_FILE, copy.deepcopy(DEFAULT_PRODUCTS))
    if not os.path.exists(CATEGORIES_FILE):
        _write_json(CATEGORIES_FILE, {"order": list(DEFAULT_CATEGORIES)})


def adjust_stock(product_id, delta):
    """상품 재고 변경(delta<0 이면 차감). 재고가 음수(-1 등)면 '무제한'으로 보고 건드리지 않음.

    반환: (변경여부, 남은재고 or None)
    """
    try:
        delta = int(delta)
    except Exception:
        return False, None
    pid = str(product_id or "").strip()
    if not pid:
        return False, None
    with _lock:
        prods = _read_json(PRODUCTS_FILE, [])
        for p in prods:
            if str(p.get("id")) == pid:
                try:
                    cur = int(p.get("stock", 0) or 0)
                except Exception:
                    cur = 0
                if cur < 0:
                    return False, None
                new = max(0, cur + delta)
                p["stock"] = new
                _write_json(PRODUCTS_FILE, prods)
                return True, new
    return False, None


def set_stock(product_id, value):
    """재고를 절대값으로 설정. (변경여부, 새 재고) 반환."""
    pid = str(product_id or "").strip()
    if not pid:
        return False, None
    try:
        val = max(0, int(value))
    except Exception:
        return False, None
    with _lock:
        prods = _read_json(PRODUCTS_FILE, [])
        for p in prods:
            if str(p.get("id")) == pid:
                p["stock"] = val
                _write_json(PRODUCTS_FILE, prods)
                return True, val
    return False, None


def seed_default_products(merge=True):
    """기본 상품(로블록스 쿠키)을 저장. merge=True 면 없는 상품만 추가."""
    cur = load_products()
    if not merge:
        out = copy.deepcopy(DEFAULT_PRODUCTS)
    else:
        out = list(cur or [])
        have = {str(p.get("id")) for p in out}
        for p in copy.deepcopy(DEFAULT_PRODUCTS):
            if str(p.get("id")) not in have:
                out.append(p)
    save_products(out)
    return out


def load_questions():
    with _lock:
        data = _read_json(QUESTIONS_FILE, {"buy": DEFAULT_QUESTIONS_BUY, "error": DEFAULT_QUESTIONS_ERROR})
        data.setdefault("buy", copy.deepcopy(DEFAULT_QUESTIONS_BUY))
        data.setdefault("error", copy.deepcopy(DEFAULT_QUESTIONS_ERROR))
        return data


def save_questions(data):
    with _lock:
        _write_json(QUESTIONS_FILE, data)


def load_settings():
    with _lock:
        data = _read_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        merged = copy.deepcopy(DEFAULT_SETTINGS)
        merged.update(data or {})
    # 저장된 값이 비어 있으면 기본 서버 ID로 복구 ('none' 이면 그대로 비활성)
    for k, v in DEFAULT_IDS.items():
        if not str(merged.get(k) or "").strip():
            merged[k] = v
    return merged


def save_settings(settings):
    with _lock:
        _write_json(SETTINGS_FILE, settings)


def load_tickets():
    with _lock:
        return _read_json(TICKETS_FILE, [])


def save_tickets(tickets):
    with _lock:
        _write_json(TICKETS_FILE, tickets)


def next_ticket_no():
    with _lock:
        tickets = _read_json(TICKETS_FILE, [])
        no = (max([t.get("no", 0) for t in tickets]) + 1) if tickets else 1
        return no


def append_ticket(record):
    with _lock:
        tickets = _read_json(TICKETS_FILE, [])
        tickets.append(record)
        _write_json(TICKETS_FILE, tickets)
        return record


def load_notices():
    with _lock:
        return _read_json(NOTICES_FILE, [])


def load_commands():
    with _lock:
        arr = _read_json(COMMANDS_FILE, [])
        return arr if isinstance(arr, list) else []


def save_commands(cmds):
    with _lock:
        _write_json(COMMANDS_FILE, cmds if isinstance(cmds, list) else [])


def save_notices(notices):
    with _lock:
        _write_json(NOTICES_FILE, notices)


def append_notice(record):
    with _lock:
        notices = _read_json(NOTICES_FILE, [])
        notices.append(record)
        _write_json(NOTICES_FILE, notices)
        return record


def init_storage():
    _ensure_dir()
    ensure_defaults()
    if not os.path.exists(QUESTIONS_FILE):
        _write_json(QUESTIONS_FILE, {"buy": DEFAULT_QUESTIONS_BUY, "error": DEFAULT_QUESTIONS_ERROR})
    if not os.path.exists(SETTINGS_FILE):
        _write_json(SETTINGS_FILE, DEFAULT_SETTINGS)
    if not os.path.exists(TICKETS_FILE):
        _write_json(TICKETS_FILE, [])
    if not os.path.exists(NOTICES_FILE):
        _write_json(NOTICES_FILE, [])
    if not os.path.exists(REVIEWS_FILE):
        _write_json(REVIEWS_FILE, [])
    if not os.path.exists(COMMANDS_FILE):
        _write_json(COMMANDS_FILE, [
            {"name": "계좌", "description": "계좌번호 안내",
             "title": "💳 입금 계좌 안내", "message": "은행: \n계좌번호: \n예금주: \n\n입금 후 입금자명을 티켓에 남겨주세요.",
             "color": 5814783, "image_url": "", "footer": "Apex Bot", "ephemeral": False, "enabled": True},
        ])
    pp = os.path.join(DATA_DIR, "review_pending.json")
    if not os.path.exists(pp):
        _write_json(pp, {})
