# Apex Bot — 티켓구매봇 Render 배포 가이드

## 0. 개요 (Apex Bot — 티켓/안내는 임베드, 구매·후기는 이미지 카드)
- 구매문의: 카테고리 선택 → 상품선택 → 질문답변 → 비공개 티켓 (구매 카테고리)
- **기본 상품 내장**: 로블록스 쿠키 **18종**(가격 포함) + 기본 카테고리 **4종**
  - `data/products.json` 이 없거나 비어 있으면(초기화·재배포) **자동으로 다시 채워집니다**
  - 이미 다른 상품이 저장돼 있으면 대시보드 → 상품 탭의 **`기본 쿠키 18종 불러오기`** 버튼으로 추가(중복 상품은 건너뜀)
- **순서 설정**: 상품별 `순서` 숫자, 카테고리 **▲▼ 순서** 를 대시보드에서 바꾸면 봇 구매창 순서에 그대로 반영
- **재고 관리**: 구매완료 시 재고가 자동 차감(갯수만큼) · 재고 0 = **품절**(구매 차단) · 재고 **-1 = 무제한**
- **입고 알림**: 재고가 늘어나면(대시보드 수정 또는 `/재고추가`) **입고 채널**에 알림 전송
- 오류문의: 질문답변 → 비공개 티켓 (오류 카테고리)
- 티켓 채널 이름/요약 임베드에 티켓 번호는 표시되지 않음 (닉네임만 사용)
- 1인 1티켓: 열린 티켓 있으면 신규 생성 차단
- `/구매완료` or ✅ 버튼: 구매자 역할 지급 + **구매 완료 카드(PNG 이미지)** + 구매로그(같은 카드 이미지) + 후기 DM(상품명 포함)
- 🔒 닫기: 사유 입력 → **채널은 삭제하지 않고 문의자에게서만 숨김(관리자 전용)** → `🗑️ 채널 삭제` 버튼으로 삭제
- 후기: DM 별점 → DM 텍스트 → 후기 채널에 **후기 카드(PNG 이미지)** 자동 등록 (상품명/카테고리 표시)
- 커스텀 명령어: 대시보드에서 `/계좌` 등 생성 → 임베드 발송
- Render: 5분 자가핑 + /health

> 카드 이미지 안내
> - 디자인: 얇은 테두리 카드 + 상단 옅은 하이라이트 + **로고 칩(이니셜) + 상태 필(결제 완료/후기 등록)** + **금액·상품 히어로 패널** + 구분선 테이블 (레퍼런스와 다른 자체 레이아웃)
> - 기본 강조색: 구매 카드 **민트**, 후기 카드 **앰버**. 대시보드 `card_accent`(HEX)로 원하는 색으로 변경 가능
> - `Pillow` 로 서버에서 직접 PNG 를 그립니다. 폰트(Pretendard)는 **최초 1회 자동 다운로드 후 `data/fonts/` 에 캐시**됩니다.
> - 이미지 생성/업로드가 불가능한 환경이면 **자동으로 V2 카드 → 임베드 카드**로 폴백하므로 실패하지 않습니다.
> - 이미지를 끄려면 대시보드 봇메시지 탭의 `card_image_enabled` 를 `false` 로 두세요.
> - 구매로그 채널(`purchase_log_channel_id`)에도 **동일한 카드 이미지 + 요약 임베드(담당/역할/구매ID)** 가 함께 전송됩니다.

## 1. 폴더
이 폴더 통째로 GitHub에 올리세요: `ticket-bot/`

## 2. Render 설정 (Web Service)
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120`
- Health Check Path: `/health`
- Environment:
  - `DISCORD_TOKEN` = 디스코드 봇 토큰
  - `GUILD_ID` = 서버 ID (슬래시 명령어 즉시 반영용)
  - `DASHBOARD_PASSWORD` = 대시보드 비밀번호
  - `KEEPALIVE` = 1
  - `KEEPALIVE_URL` = Render 주소 (예: https://xxx.onrender.com) — 5분마다 /ping 자가호출

- 정적 파일/폰트 캐시(`data/fonts/`)는 `.gitignore` 처리 · 재배포 시 자동 재다운로드

## 3. 디스코드 봇 설정
- Privileged Intents: Server Members Intent ON
- 권한: Manage Channels, Send Messages, Embed Links, **Attach Files**, Read History, **Manage Roles(역할 관리)**
  - 구매완료/후기 카드는 **PNG 이미지 업로드**라 `Attach Files`(파일 첨부) 가 필요합니다.
  - 구매자 역할 지급에는 *역할 관리* 권한이 필요하고, **봇의 최상위 역할이 지급할 역할보다 위**에 있어야 합니다.
  - 권한/서열 문제가 있으면 구매완료 시 어떤 문제인지(`❌ ...`) 그대로 알려줍니다.
- 관리자 역할 ID를 대시보드 Settings(admin_role_id)에 입력

### 서버 기본 ID (코드에 내장 · 초기화/재배포 후에도 자동 적용)
| 설정 키 | 기본값 |
|---|---|
| `ticket_category_id` / `buy_category_id` / `error_category_id` | `1538518399066308668` |
| `ticket_log_channel_id` | `1538072438691332177` |
| `purchase_log_channel_id` | `1537817248457170964` |
| `review_channel_id` | `1537817307475349554` |
| `buyer_role_id` | `1538126406662225981` |

- 대시보드에서 **비우면 자동으로 위 기본값이 적용**되고, 다른 값으로 바꾸면 그 값이 우선입니다.
- 해당 기능을 끄고 싶으면 값을 **`none`** 으로 두세요(숫자가 아니면 무시).

## 4. 사용법 (전부 임베드)
- `/panel` (관리자) → 고급 패널 전송 (이미지/썸네일 지원, 상품목록 숨김)
- 구매문의 → 카테고리 선택 → 상품선택 임베드 → 질문 → 티켓+요약임베드+DM임베드
- 오류문의 → 질문 → 티켓+요약임베드+DM임베드
- ✅ 구매완료 (버튼 or `/구매완료`): 역할지급 + **구매 완료 카드** + 구매로그 + 후기DM
  → 채널은 유지되고 문의자는 읽기 전용, `🗑️ 채널 삭제` 버튼으로 정리
- 🔒 닫기 (버튼 or `/ticket-close [사유]`): 사유 채널/로그/DM → 채널은 삭제되지 않고 **관리자에게만 보임**
  → `🗑️ 채널 삭제` 버튼을 눌러야 실제 삭제
- 후기: DM 별점 버튼 → DM에 후기 작성 → 후기 채널에 **후기 카드** 등록 (작성자/카테고리/상품/별점/티켓 표시)
- 🎁 `/상품지급 [member] [product] [content] [file]` (관리자): 입력한 상품 내용을 대상 **DM 카드**로 전송
  - 티켓 채널에서 실행하면 대상이 티켓 주인으로 자동 지정
  - 내용을 비우고 실행하면 **긴 글 입력창(모달)** 이 열림
  - 긴 텍스트는 `file`(txt/md)로 첨부 가능 · 줄바꿈 그대로 전송되고, 3,500자를 넘으면 카드 미리보기 + **전체 txt 파일** 첨부
- 🧪 `/역할테스트 [member]` (관리자): 구매자 역할 지급이 가능한지 점검 (역할 ID / 봇 권한 / 역할 서열 / 실제 지급 후 원복)
- 📦 `/재고추가 상품:<이름검색> 수량:<n>` (관리자): 재고를 늘리고 **입고 알림**을 입고 채널로 전송
  - 입고 채널: 대시보드 `stock_log_channel_id` (비우면 구매로그 → 티켓로그 순서로 대체)
  - 대시보드에서 상품 재고를 **늘려서 저장**해도 자동으로 입고 알림이 갑니다
- `/announce` `/dm-test` `/cmd-reload` (관리자)

## 5. 대시보드 (Pro)
- 상단 통계 + 탭: 상품 / 질문 / 명령어 / 봇메시지 / DM / 공지 / 티켓
- 상품: 이름/카테고리/가격/갯수/할인/재고/판매중 + **순서(숫자)** · 카테고리 순서(▲▼) · `기본 쿠키 18종 불러오기`
  (카테고리가 2개 이상이면 봇에서 카테고리 선택 단계가 생기고, **카테고리·상품 모두 설정한 순서대로** 표시)
  재고를 늘려 저장하면 **입고 알림**이 입고 채널로 자동 전송됩니다.
- 질문: 구매/오류 각 5개
- 명령어: 이름(예: 계좌) + 제목/내용/색상/이미지/나만보기/관리자만 → 저장 후 `/cmd-reload`
- 봇메시지: 패널/카테고리(구매/오류)/로그/구매로그/후기채널/역할/완료문구/후기문구 + 카드 제목·안내문·브랜드(`receipt_brand`)·강조색(`card_accent`)·이미지 사용(`card_image_enabled`)
- DM: 열림/닫힘 ON·제목·내용
- 공지: 미리보기 → `/announce` 발송
- 티켓: 상태(open/completed/closed) + 사유/완료자

## 6. 로컬 실행
```
pip install -r requirements.txt
python app.py
```
- 웹: http://localhost:10000 , 대시보드: http://localhost:10000/dashboard

## 7. 실행 파일 목록
- app.py / bot_main.py / bot_cmds.py / custom_cmds.py
- ui_modal.py / ui_panel.py / ui_control.py / ui_close.py / ui_complete.py / ui_done.py / ui_review.py / ui_receipt.py / ui_gift.py / ui_card_render.py / ui_stock.py
- ticket_utils.py / store.py / web.py / dash_api.py
- templates/dash_pro.html + static/dash_core.js + static/dash_prod.js + static/dash_q.js

## 8. 재배포 (git lock시)
```
cd "c:\Users\USER\Downloads\PylaAI-main (1)\ticket-bot"
del .git\index.lock
git add -A
git commit -m "Apex Bot update"
git push origin main
```
- Render 자동 재배포 후 `/panel` 다시 전송 (새 버튼 반영)


