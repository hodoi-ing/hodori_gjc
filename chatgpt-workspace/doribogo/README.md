# 🐯 도리보고 (Doribogo) v4.5.0 — 실시간 팩트 큐레이션 & 디스코드 챗봇

> **2단계 순차 교차검증(1차 공식 SNS ➔ 2차 언론 검증) & 디스코드 실시간 양방향 챗봇 (`hodori bot`) 정식 가동**  
> *Primary Truth First • Cross-Verification • 4-Step Fact Format • Discord Interactive & 24/7 Cloud Actions*

[![Version](https://img.shields.io/badge/version-4.5.0-orange.svg?style=flat-square)](https://github.com/hodoi-ing/hodori_gjc)
[![Discord Bot](https://img.shields.io/badge/Discord_Bot-hodori_bot_ONLINE-green.svg?style=flat-square)]()
[![Engine](https://img.shields.io/badge/Architecture-2--Stage_Sequential_Verification-blue.svg?style=flat-square)]()
[![AI Model](https://img.shields.io/badge/AI_Engine-Gemini_2.5_Flash-purple.svg?style=flat-square)]()
[![Cloud Cron](https://img.shields.io/badge/GitHub_Actions-24%2F7_Automated-brightgreen.svg?style=flat-square)]()

---

## 📌 1. 프로젝트 개요 (Overview)

**도리보고(Doribogo) v4.5.0**은 기존 검색 엔진들의 단편적이고 오래된 블로그 낚시성 글을 배제하고, **1차 공식 원문(기업 공식 X·스레드 계정)을 먼저 확보한 뒤 2차 언론사 보도로 교차 검증**하는 차세대 실시간 정보 수집 & AI 팩트 큐레이션 엔진입니다.

현재 디스코드 서버에서 **`hodori bot`**이라는 이름으로 24시간 실시간 동작 중이며, 채팅창에서 명령어를 치는 즉시 3초 만에 4단계 고밀도 리포트를 회신합니다.

---

## 🏛️ 2. 2단계 순차 교차검증 아키텍처 (2-Stage Verification Pipeline)

```
[1단계: 1차 원문 팩트 확보 (Primary Ground Truth)] ➔ 최우선 탐색!
  • 기업/개발사 공식 발표 및 공식 X·스레드 계정 (@Zai_org, @deepseek_ai, @OpenAI, @AnthropicAI 등)
  • 최신 신규 모델 출시 및 실시간 특가 공지 (GLM-5.3-Flash, 1/10 비용, 스펙 원문 팩트)
        ▼
[2단계: 2차 언론 & 시장 교차검증 (Secondary Cross-Verification)]
  • 주요 IT 언론사 속보 및 테크 미디어 기사 대조
  • 국내외 개발자 커뮤니티(레딧, 펨코, 디시, 클리앙) 실사용자 벤치마크 검증
        ▼
[3-Tier 중복 제거 & Jaccard 유사도 필터링] ➔ 노이즈 및 중복 기사 100% 압축
        ▼
[Gemini 2.5 Flash가 1차 팩트 + 2차 검증을 대조하여 4단계 리포트 완성]
```

---

## 💬 3. 디스코드 실시간 챗봇 (`hodori bot`) 사용법

디스코드 채팅창에 `!도리 [키워드]`를 입력하면 그 자리에서 즉시 답장합니다:

```text
!도리 중국 AI 모델 최신 이슈
!도리 백컨트리 360 특가
!도리 RTX 5090 가격
!도리 오픈AI 최신 소식
!도리 도움말
```

### 📋 출력되는 지정 4단계 팩트 규격
```text
⚡ [08월 30일 실시간 이슈] 키워드

🔥 [정제된 세련된 주제명 • 08월 30일]

1. 🚨 최신 이슈
- 오늘/최근 24시간 이내에 발생한 가장 중요한 핵심 팩트 1~2줄 요약

2. 📌 구체적인 설명
- 단순 제목 나열 금지! 1차 공식 팩트와 2차 언론 검증을 종합한 구체적인 배경, 수치/비용, 핵심 스펙, 시장 영향을 4~6문장으로 깊이 있게 서술

3. 🗣️ 사람들 반응
• 💬 "실제 개발자/수강생/실사용자 호평 또는 기대 멘트"
• ⚠️ "실제 주의점 또는 비판/우려 멘트"

4. 🔗 실제 내용 출처
• https://실제_기사_또는_공식_SNS_원문_링크
```

---

## ☁️ 4. 24/7 클라우드 무인 자동화 (GitHub Actions)

- **주기**: 매 30분마다 24시간 자동 실행 (`.github/workflows/doribogo_cron.yml`)
- **기능**: 내 컴퓨터가 꺼져 있어도 클라우드 서버가 30분마다 깨어나 감시 키워드(백컨트리 360, 특가 등)를 탐색 후 디스코드로 6장 카드뉴스 자동 발송
- **비용**: 0원 (GitHub Actions 무료 티어 + Google Gemini Free API)

---

## 📁 5. 프로젝트 파일 구성

```
hodori_gjc/
├── chatgpt-workspace/doribogo/
│   ├── doribogo_bot.py            # 2단계 교차검증 & 4단계 팩트 큐레이션 코어
│   ├── discord_interactive_bot.py # 디스코드 양방향 실시간 챗봇 (hodori bot)
│   ├── universal_harvester.py     # 5대 멀티 레이더 원본 수집기
│   ├── AUTONOMOUS_DISCOVERY.md    # 자율 탐색 아키텍처 명세서
│   └── README.md                  # 본 기술 설명서
├── .github/workflows/
│   └── doribogo_cron.yml          # 24/7 클라우드 30분 무인 크론 워크플로우
└── .env                           # 로컬 봇 토큰 및 API 키 보안 파일
```
