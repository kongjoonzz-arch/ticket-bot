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

_lock = threading.Lock()

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
    "buy_category_id": "",
    "error_category_id": "",
    "ticket_category_id": "",
    "ticket_log_channel_id": "",
    "purchase_log_channel_id": "",
    "review_channel_id": "",
    "buyer_role_id": "",
    "one_ticket_per_user": True,
    "complete_button_label": "✅ 구매완료",
    "complete_title": "✅ 구매완료 처리",
    "complete_message": "구매가 완료되었습니다. 이용해 주셔서 감사합니다!",
    "complete_log_title": "✅ 구매완료",
    "review_dm_title": "⭐ 후기를 남겨주세요! (티켓 #{no})",
    "review_dm_message": "안녕하세요 {user_mention}님!\n**{product}** 구매가 완료되었습니다 🎉\n\n아래에서 별점을 골라주세요. 그 다음 DM으로 후기를 적어주시면 후기 채널에 자동 등록됩니다.",
    "review_title_format": "⭐ {stars} · {user}",
    "review_min_length": 5,
    "admin_role_id": "",
    "mention_admin_on_create": True,
    "mention_text": "📢 관리자님, 새 티켓이 열렸습니다! {admin_mention} 확인 부탁드립니다.",
    "welcome_message": "안녕하세요 {user_mention}님! 문의 내용을 정리해드렸어요.\n관리자가 곧 확인해드립니다. 추가 설명이 있으면 이 채널에 적어주세요 🙂",
    "close_message": "🔒 티켓이 닫혔습니다. 이용해 주셔서 감사합니다!",
    "delete_on_close": True,
    "delete_delay_sec": 5,
    "ticket_button_label": "🔒 티켓 닫기",
    "dm_on_open": True,
    "dm_open_title": "🎫 티켓이 열렸습니다! (#{no})",
    "dm_open_message": "안녕하세요 {user_mention}님!\n{kind} 티켓 **#{no}**이 열렸습니다.\n{channel} 에서 대화를 이어가주세요.\n\n{product}\n\n{answers}",
    "dm_on_close": True,
    "dm_close_title": "🔒 티켓이 닫혔습니다. (#{no})",
    "dm_close_message": "안녕하세요 {user_mention}님!\n티켓 **#{no}** ({kind}) 이 닫혔습니다.\n\n📌 닫기 사유: {reason}\n\n추가 문의가 있으면 새 티켓을 열어주세요 🙂",
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
    if not os.path.exists(PRODUCTS_FILE):
        _write_json(PRODUCTS_FILE, [
            {"id": "p1", "name": "예시 상품 A", "price": 10000, "stock": 50,
             "description": "대시보드에서 수정하세요.", "enabled": True},
        ])
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
