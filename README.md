# Apex Bot — 티켓구매봇 Render 배포 가이드

## 0. 개요 (Apex Bot — 모든 메시지는 임베드)
- 구매문의: 상품선택 → 질문답변 → 비공개 티켓 (구매 카테고리)
- 오류문의: 질문답변 → 비공개 티켓 (오류 카테고리)
- 1인 1티켓: 열린 티켓 있으면 신규 생성 차단
- `/구매완료` or ✅ 버튼: 구매자 역할 지급 + 구매로그 + 후기 DM(별점) → 채널 삭제
- 🔒 닫기: 사유 입력 → 채널/로그/DM 전달 → 채널 삭제 (구매완료 아님)
- 후기: DM 별점 → DM 텍스트 → 후기 채널 임베드 자동 등록
- 커스텀 명령어: 대시보드에서 `/계좌` 등 생성 → 임베드 발송
- Render: 5분 자가핑 + /health

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

## 3. 디스코드 봇 설정
- Privileged Intents: Server Members Intent ON
- 권한: Manage Channels, Send Messages, Embed Links, Read History
- 관리자 역할 ID를 대시보드 Settings(admin_role_id)에 입력

## 4. 사용법 (전부 임베드)
- `/panel` (관리자) → 고급 패널 전송 (이미지/썸네일 지원, 상품목록 숨김)
- 구매문의 → 상품선택 임베드 → 질문 → 티켓+요약임베드+DM임베드
- 오류문의 → 질문 → 티켓+요약임베드+DM임베드
- ✅ 구매완료 (버튼 or `/구매완료`): 역할지급 + 구매로그 + 후기DM → 채널 삭제
- 🔒 닫기 (버튼 or `/ticket-close [사유]`): 사유 채널/로그/DM → 채널 삭제 (구매완료 아님)
- 후기: DM 별점 버튼 → DM에 후기 작성 → 후기 채널 임베드 등록
- `/announce` `/dm-test` `/cmd-reload` (관리자)

## 5. 대시보드 (Pro)
- 상단 통계 + 탭: 상품 / 질문 / 명령어 / 봇메시지 / DM / 공지 / 티켓
- 상품: 이름/가격/재고/판매중
- 질문: 구매/오류 각 5개
- 명령어: 이름(예: 계좌) + 제목/내용/색상/이미지/나만보기/관리자만 → 저장 후 `/cmd-reload`
- 봇메시지: 패널/카테고리(구매/오류)/로그/구매로그/후기채널/역할/완료문구/후기문구 전부 수정
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
- ui_modal.py / ui_panel.py / ui_control.py / ui_close.py / ui_complete.py / ui_done.py / ui_review.py
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


