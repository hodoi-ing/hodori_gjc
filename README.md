# 🔒 hodori_gjc (호도리 전용 GJC 통합 안전 저장소)

> 📅 마지막 업데이트: 2026-08-28

본 저장소는 GJC(Gajae Code) 하네스, OMGC 확장 프레임워크, 허예찬님의 공식 **`gajae-code`** 원본 소스, 그리고 노션 **`ONTOLOGY`** 규칙을 하나로 통합한 비공개 저장소입니다.

---

## 📌 핵심 구성 요소 & 가이드 (Single Source of Truth)

1. 📜 **`PROTOCOL.md`**: GJC 하네스 & ChatGPT 커넥터 간의 공동 작업 수칙
2. 🧠 **`ONTOLOGY.md`**: 호도리 온톨로지 및 AI 운영 센터 지침 (가치관, 수익/자동화 방향, 승인 규칙)
3. ✍️ **`IM_NOT_AI.md`**: 로봇 말투/상투어 전면 제거 및 인간형 글쓰기 가이드
4. 🦀 **`gajae-code/`**: 공식 Gajae Code (Yeachan-Heo/gajae-code) 원본 전체 백업 및 참조 소스
5. 🚀 **`oh-my-gajae-code/`**: OMGC 멀티 에이전트 프레임워크 및 안전 운영 도구
6. 🕷️ **안전 네이버 수집기 스크립트**:
   - `safe_naver_scraper.py` (제재 방지 5대 수칙 적용 통합 스크래퍼)
   - `fetch_hot_news.py` (네이버 사회 분야 실시간 핫뉴스 수집기)
   - `naver_crawler.py` & `naver_blog_scraper.py` (실시간 검색 및 모바일 본문 수집기)

---

## 🛡️ 보안 규칙
1. API Key, SSH Key, 개인 토큰(`.env`, `mcp.json` 등)은 절대로 Git에 커밋하지 않습니다. (Pre-Commit Hook으로 100% 자동 검사)
2. 모든 작업은 Private 상태를 유지합니다.

---

## 🐯 GPT 호도리 제작소

ChatGPT와 호도리가 함께 아이디어를 만들고, 작은 실험으로 검증하면서 실제 프로젝트로 발전시키는 작업 공간입니다.

### 📁 작업 공간

`chatgpt-workspace/`

이 폴더 안에는 ChatGPT와 함께 설계·검증 중인 프로젝트와 실험 기록을 관리합니다.

<details open>
<summary>🐯 도리보고 (v6.0.0) — CHOI 스타일 스레드 큐레이션 & 디스코드 hodori bot 가동 중!</summary>

### 🐯 도리보고 (Doribogo `v6.0.0`) & 디스코드 챗봇 (`hodori bot`)

**위치:** `chatgpt-workspace/doribogo/` & `doribogo_bot.py`  
**디스코드 봇:** `hodori bot` (자연어 대화 `도리야 [질문]` 및 명령어 `!도리 [키워드]` 활성화)

> 요리보고 저리보고, **도리보고!**

Threads 30만 팔로워 AI 인플루언서 **`CHOI (@choi.openai)`**의 **[4단 연쇄 스레드 큐레이션 포맷]**과 **[5대 다각도 이슈 레이더]**를 전면 이식하여, 어떤 키워드든 공식 발표의 허점을 찌르는 날카로운 팩트 분석과 실무 수치 환산 리포트를 디스코드로 실시간 전송합니다.

#### 🔀 5대 핵심 아키텍처

1. **5대 다각도 이슈 탐지 레이더 (5-Way Issue Radar)**:
   - **📱 1) 공식 SNS & 릴리즈 속보**: 기업 공식 X·스레드 계정 및 엔지니어 개인 피드 최우선 스캔.
   - **🔍 2) 숨은 각주 & 쿼터/비용 정책 Diffing**: 쿼터 축소, 가격 인상, 사용량 공유, 토큰 누수 버그 포착.
   - **🛠️ 3) 오픈소스 & 가중치/보안**: 모델 가중치 수정, MoE, LoRA, JailbreakBench 벤치마크 추적.
   - **⚡ 4) 에이전트 표준 & 인프라**: WebMCP, MCP, 브라우저 자동화 등 새로운 웹/개발 표준 추적.
   - **💰 5) 실시간 특가 & 역대가**: 캠핑/하드웨어 역대가, 대란, 타임딜 실시간 탐지.
2. **CHOI (@choi.openai) 4단 연쇄 스레드 큐레이션 포맷**:
   - **📌 [메인 본문]**: 1행 역발상 훅 + 2~3줄 요약 + 반전 대조 (*"표현은 A이지만 결국 B인 셈"*)
   - **💬 [댓글 1 | 기술 메커니즘 딥다이브]**: 아키텍처, 버그 지점, 가중치/로직 변경 등 기술 원인 서술
   - **💬 [댓글 2 | 체감 수치 환산 & 실무 영향]**: 100 기준 직관적 정수 환산 + 실무 대응 전략
   - **💬 [댓글 3 | 공식 출처]**: 1차 원문 검증 링크 (알고리즘 페널티 회피형)
3. **디스코드 실시간 양방향 챗봇 (`hodori bot`)**:
   - **자연어 호출**: `도리야 [질문]`, `호도리야 [질문]`, `@hodori bot [질문]`
   - **명령어 호출**: `!도리 [키워드]`, `!ai [질문]`
   - **24/7 백그라운드 데몬**: 무중단 실시간 질의응답 및 자동 레이더 모니터링.
4. **최근 24~72시간(`when:7d`) 엄격 최신성 & 3-Tier Jaccard 유사도 필터**:
   - 과거 구버전 기사를 원천 차단하고 중복 기사 100% 압축.
5. **멀티 모델 Gemini 2.5 Flash 엔진 & 오프라인 폴백 탑재**.

#### ⚙️ 디스코드 봇 설정 및 환경 변수 (`.env`)

```env
DISCORD_BOT_TOKEN="디스코드_봇_토큰"
DISCORD_CHANNEL_ID="자동_알림_채널_ID"
DISCORD_WEBHOOK_URL="디스코드_웹후크_URL"
TELEGRAM_BOT_TOKEN="텔레그램_봇_토큰"
TELEGRAM_CHAT_ID="텔레그램_채팅_ID"
GEMINI_API_KEY="구글_제미나이_API_키"
```

#### 🚀 봇 실행 및 백그라운드 가동

```bash
# 1. 디스코드 대화형 비서 실행 (포그라운드)
python3 discord_interactive_bot.py

# 2. 백그라운드 무중단 데몬 가동 (nohup)
nohup python3 discord_interactive_bot.py > /tmp/discord_bot.log 2>&1 &

# 3. 단일 키워드 CLI 즉시 리서치
python3 -c "import doribogo_bot; print(doribogo_bot.run_full_doribogo('Claude Code 사용량'))"
```

상세 설계와 기술 문서는 [`chatgpt-workspace/doribogo/README.md`](chatgpt-workspace/doribogo/README.md)에서 관리합니다.

</details>
<details>
<summary>📄 HWP 자동화 — 자세히 보기</summary>

### 📄 HWP 자동화 프로젝트 (반자동화)

**위치:** `chatgpt-workspace/hwp-automation/`

여러 HWP/HWPX 문서를 읽고, 타깃 문서의 표·누름틀에 **내용만 자동으로** 정리하는 반자동화(Human-in-the-Loop) 프로젝트입니다.

**핵심 원칙: 내용은 자동으로, 구조는 승인 후에.**

- 표/누름틀의 기하 구조(행·열·병합·위치)는 그대로 두고 `{{키}}` 플레이스홀더의 값만 치환합니다.
- 표 병합·행 추가 등 구조 변경이 필요한 순간에는 사용자 승인을 받은 뒤에만 진행합니다.

#### ✅ 실동작 엔진 (로컬 검증 완료)

`chatgpt-workspace/hwp-automation/hwp_bridge.py` (CLI, `python3`)

```bash
python3 hwp_bridge.py --read   문서.hwpx                    # 읽기/분석
python3 hwp_bridge.py --fill   문서.hwpx '{"이름":"홍길동"}'  # 값만 채우기
python3 hwp_bridge.py --verify 문서.hwpx                    # 무결성 검증
```

- 원본은 절대 안 바뀌고, 결과는 `<원본>_수정본.hwpx`로 생성됩니다.
- 반복 실행(재채우기)도 매번 원본 템플릿 기준으로 동작합니다.

#### 🧩 사용 엔진

- `python-hwpx-automation` → 내용 주입(바이트 보존 `paragraph_patch`) + 읽기 + 검증 (실사용)
- `syhwp` → 보조 파서
- `pyhwpx` → 표 병합/행 추가 등 구조 변경 (Windows + 한글 설치 환경에서만)

#### 🛠️ 구조 변경 (표 병합/행 추가) — XML 기반으로 완전 지원

- 표 병합(`merge_table`), 행 추가(`insert_row_by_clone`), 행 삭제, 표 분리(`split_table`)가 전부 **XML 레벨에서 동작**합니다. (Windows/OLE 불필요)
- 구조 변경은 **승인 게이트**를 거칩니다: `--plan`(dry-run, 승인 근거 transcript) → 사용자 승인 → `--apply`(실행).

#### ⚠️ 남은 제약

- 구형 `.hwp`(바이너리)는 `.hwpx` 변환 후에만 처리 가능합니다.
- 중첩 표(표 안의 표)는 구조 변경이 불가합니다(fail-closed).

#### 📚 설계 문서

- `SEMI_AUTOMATION.md` — 반자동화 운영 규약 (승인 게이트)
- `ZERO_TOUCH_CHALLENGES.md` — 자동 구간 기술 장애물 해결서
- `TEMPLATE_PROTOCOL.md` — 템플릿 작성 규칙
- `skills/hwp/SKILL.md` — GJC 실제 호출 스킬

상세 설계와 진행 기준은 [`chatgpt-workspace/hwp-automation/README.md`](chatgpt-workspace/hwp-automation/README.md)에서 관리합니다.

</details>