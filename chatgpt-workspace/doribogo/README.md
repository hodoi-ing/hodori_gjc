# 🐯 도리보고 (Doribogo) v6.0.0 — CHOI 스타일 스레드 큐레이션 & 디스코드 hodori bot

> **CHOI (@choi.openai) 4단 연쇄 스레드 큐레이션 & 5대 다각도 이슈 레이더 탑재**  
> *5-Way Radar • 4-Stage Thread Curation • Discord Interactive Assistant (`hodori bot`)*

[![Version](https://img.shields.io/badge/version-6.0.0-orange.svg?style=flat-square)](https://github.com/hodoi-ing/hodori_gjc)
[![Discord Bot](https://img.shields.io/badge/Discord_Bot-hodori_bot_ONLINE-green.svg?style=flat-square)]()
[![Engine](https://img.shields.io/badge/Architecture-5--Way_Issue_Radar-blue.svg?style=flat-square)]()
[![AI Model](https://img.shields.io/badge/AI_Engine-Gemini_2.5_Flash-purple.svg?style=flat-square)]()
[![Style](https://img.shields.io/badge/Style-CHOI_Thread_Format-red.svg?style=flat-square)]()

---

## 📌 1. 프로젝트 개요 (Overview)

**도리보고(Doribogo) v6.0.0**은 Threads 30만 인플루언서 **`CHOI (@choi.openai)`**의 콘텐츠 작법과 이슈 발굴 메커니즘을 100% 이식한 차세대 실시간 정보 수집 & AI 팩트 큐레이션 엔진입니다.

기업들의 마케팅성 발표 이면에 숨겨진 **실제 수치 삭감, 정책 변경, 쿼터 공유, 가중치 버그**를 날카롭게 파헤치고, 디스코드 채팅창에서 실시간으로 대화하며 4단 분리 고밀도 스레드 리포트를 제공합니다.

---

## 🏛️ 2. 5대 다각도 이슈 탐지 레이더 (5-Way Issue Radar)

```
[1. 📱 공식 SNS & 릴리즈 속보]
  • 기업 공식 X·스레드 계정 및 핵심 엔지니어 개인 피드 최우선 스캔

[2. 🔍 숨은 각주 & 쿼터/비용 정책 Diffing]
  • 가격표 하단 작은 글씨(Fine Print), 사용량 공유, 쿼터 축소, 토큰 누수 역추적

[3. 🛠️ 오픈소스 & 가중치/보안 벤치마크]
  • 모델 가중치 수정(Weights Diffing), MoE, LoRA, JailbreakBench 벤치마크 추적

[4. ⚡ 에이전트 표준 & 인프라]
  • WebMCP, MCP, 브라우저 자동화 등 새로운 웹/개발 표준 변화 추적

[5. 💰 실시간 특가 & 역대가]
  • 캠핑 텐트, IT 하드웨어 역대가, 대란, 타임딜 실시간 탐지
```

---

## 💬 3. 디스코드 자연어 챗봇 (`hodori bot`) 사용법

디스코드 채팅창에서 사람에게 말하듯 편하게 부르면 즉시 4단 스레드 리포트로 답장합니다.

### 💡 자연어 호출 (추천)
```text
• 도리야 Claude Code 사용량 이슈 알려줘
• 도리야 WebMCP가 뭐야?
• 도리야 백컨트리 360 특가 찾아줘
• 도리야 파이썬 비동기 코드 짜줘
• @hodori bot [질문]
```

### 📋 명령어 접두사 호출 (호환)
```text
• !도리 [키워드]  ➔ 5대 레이더 4단 스레드 리포트
• !ai [질문]      ➔ Gemini 2.5 Flash 일반 질의응답
```

---

## 📋 4. 출력되는 CHOI 스타일 4단 연쇄 스레드 규격

```text
🔥 [Claude Code 주간 사용량 25% '인상'의 숨겨진 진실 • 08월 30일]

📌 [메인 본문]
앤트로픽이 클로드 코드 주간 한도를 25% 인상한다고 발표했지만, 실제 개발자들의 체감 사용량은 17% 삭감되었습니다.

기존 50% 프로모션 혜택이 종료되고 기본 한도 대비 25%가 영구 적용되면서 발생하는 구조적 차이입니다.

표현은 '인상'이지만, 결국 '실질적 삭감'인 셈입니다.

💬 [댓글 1 | 기술 메커니즘 딥다이브]
내부 구조와 기술적 원인은 이렇습니다.
• 9월 14일부로 50% 한시 부스트가 종료되며, 기본 한도 대비 25% 인상안이 고정 적용됩니다.
• 코드 토큰 처리 로직 및 캐시 수명 만료 정책이 겹쳐 실질적인 사용 가능 횟수가 제한됩니다.

💬 [댓글 2 | 체감 수치 환산 & 실무 영향]
실제 체감 기준으로 계산하면:
• 기본 100 기준: 기존 150(50% 프로모션) ➔ 변경 후 125(25% 영구 인상)
• 결과적으로 기존 대비 주간 한도가 약 17% 줄어드는 차이가 발생합니다. 앞으로 장기 세션 작업 시 프롬프트 캐시 만료 전 /compact 명령어 사용이 필수적입니다.

💬 [댓글 3 | 공식 출처]
🔗 https://www.anthropic.com/news/claude-code-limits
```

---

## ⚙️ 5. 환경 변수 설정 (`.env`)

```env
DISCORD_BOT_TOKEN="디스코드_봇_토큰"
DISCORD_CHANNEL_ID="자동_알림_채널_ID"
DISCORD_WEBHOOK_URL="디스코드_웹후크_URL"
TELEGRAM_BOT_TOKEN="텔레그램_봇_토큰"
TELEGRAM_CHAT_ID="텔레그램_채팅_ID"
GEMINI_API_KEY="구글_제미나이_API_키"
```

---

## 🚀 6. 실행 명령어

```bash
# 1. 디스코드 대화형 비서 데몬 백그라운드 구동
nohup python3 discord_interactive_bot.py > /tmp/discord_bot.log 2>&1 &

# 2. 단일 키워드 CLI 즉시 리서치
python3 -c "import doribogo_bot; print(doribogo_bot.run_full_doribogo('WebMCP'))"
```
