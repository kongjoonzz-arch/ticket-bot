# Ticket Bot (구매문의/오류문의) — Render 배포 가이드

## 0. 개요
- 자판기 완전 제거, 티켓구매봇으로 새로 제작
- 구매문의: 상품선택 → 질문답변 → 비공개 티켓 생성
- 오류문의: 질문답변 → 비공개 티켓 생성
- 티켓 상단: 선택상품 + 답변정리 임베드 + 관리자 멘션(설정 가능)
- 티켓 내부 버튼: 구매확인/닫기 = 관리자만
- 티켓 채널: 관리자 + 티켓 연 사람만 열람
- 대시보드: 상품/질문/패널문구/멘션/티켓현황 전부 관리
- Render: 5분마다 /ping 자가호출 + /health 헬스체크

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

## 4. 사용법
- `/panel` (관리자) → 패널 전송
- 유저: 구매문의 → 상품선택 → 질문답변 → 비공개 티켓 생성 + 유저 DM 알림
- 유저: 오류문의 → 질문답변 → 비공개 티켓 생성 + 유저 DM 알림
- 티켓 상단: 답변 정리 임베드 + 관리자 멘션(설정 가능)
- 티켓 내부 버튼: 구매확인/닫기 = 관리자만
- 닫기: 사유 모달 입력 → 채널/로그/유저DM에 사유 전달 + 채널 잠금
- `/ticket-confirm`, `/ticket-close [사유]`, `/announce`, `/dm-test` (관리자)

## 5. 대시보드 (Pro)
- `https://주소/dashboard` → 비밀번호 로그인
- 상단 통계: 열린/닫힌 티켓, 판매중 상품, 공지 발송 수
- Products: 상품/가격/재고/판매중 관리
- Questions: 구매/오류 질문 최대 5개씩 관리
- 봇 메시지: 패널/버튼/멘션/환영/닫기/사유 문구 전부 수정
- DM 알림: 열림/닫힘 DM ON·제목·내용 전부 수정 ({no} {kind} {reason} 등 변수 지원)
- 공지: 제목/내용/색상/이미지/하단/멘션 + 미리보기 → 디스코드 `/announce`로 발송
- Tickets: 티켓 현황 + 닫기 사유 확인

## 6. 로컬 실행
```
pip install -r requirements.txt
python app.py
```
- 웹: http://localhost:10000 , 대시보드: http://localhost:10000/dashboard

## 7. 실행 파일 목록
- app.py / bot_main.py / bot_cmds.py
- ui_modal.py / ui_panel.py / ui_control.py
- ticket_utils.py / store.py / web.py / dash_api.py
- templates/dash2.html + static/dash_core.js + static/dash_prod.js + static/dash_q.js

