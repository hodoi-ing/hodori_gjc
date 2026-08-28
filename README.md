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
<summary>🐯 도리보고 (v3.5.0) — 자세히 보기</summary>

### 🐯 도리보고 (Doribogo `v3.5.0`)

**위치:** `chatgpt-workspace/doribogo/`

> 요리보고 저리보고, **도리보고!**

어떤 키워드든(주식, 특가할인, 정치, 경제, IT, 브랜드명 등) 던지면 **5대 다각도 레이더(공식 SNS · 특가 · 게릴라 · 스펙 · 여론)**가 동시에 가동되어 실시간 핫이슈를 낚아채고, SNS(스레드/인스타그램)에 즉시 올릴 수 있는 **6장 슬라이드 카드뉴스**로 가공해 주는 전천후 리서치 엔진입니다.

#### 🔀 4대 핵심 아키텍처

1. **5대 다각도 시그널 매트릭스 (`universal_harvester.py`)**:
   - 단일 키워드 입력 시 5개 스레드가 `[📱공식SNS · 💰특가대란 · ⚡게릴라사건 · 🛠️스펙출시 · 🗣️여론꿀팁]`을 동시 타격.
   - 인스타그램, X, 스레드 브랜드 공식 계정 피드 최우선 가산점(`+15.0`) 부여.
2. **insane-search 3단계 WAF 관통 파이프라인**:
   - 1차 크롬 120 UA 직통 ➔ 2차 Jina Reader(`r.jina.ai`) 글로벌 프록시 ➔ 3차 네이버 모바일/X 신디케이션 자동 우회로 차단 없는 본문 수집.
3. **최근 48시간(`when:2d`) 엄격 최신성 & TOP 1~6 가변 정렬**:
   - 과거 기사 유입을 원천 차단하고, 발생 시각(Hours Ago) 기준 초신선도 가중치로 최신 속보 1위 배치 (0~6개 가변 추출).
4. **SNS 6장 슬라이드 카드뉴스 포맷 (`CARD_FORMAT.md` v3.0)**:
   - `1장 표지(훅) ➔ 2장 사건 발단(팩트) ➔ 3장 핵심 포인트(비교) ➔ 4장 현장 반응(여론) ➔ 5장 호도리 시선(가이드) ➔ 6장 출처(CTA)` 장당 1메시지 슬롯 규격 및 `IM_NOT_AI.md` 엄격 준수.

#### 🚀 빠른 실행 (CLI)

```bash
# 1. 주식/경제 분야 실시간 핫이슈 카드뉴스
python3 chatgpt-workspace/doribogo/universal_harvester.py "금융투자소득세"

# 2. 브랜드 공식 SNS & 특가 대란 탐색
python3 chatgpt-workspace/doribogo/universal_harvester.py "다이슨"

# 3. 테크/오픈소스 게릴라 핫이슈 탐색
python3 chatgpt-workspace/doribogo/universal_harvester.py "OpenCode Go"

# 4. GJC / omp 단축 스킬 실행
/doribogo 아이폰 16 할인
```

상세 설계와 기술 문서는 [`chatgpt-workspace/doribogo/README.md`](chatgpt-workspace/doribogo/README.md), [`SEARCH_ARCHITECTURE.md`](chatgpt-workspace/doribogo/SEARCH_ARCHITECTURE.md), [`CHANGELOG.md`](chatgpt-workspace/doribogo/CHANGELOG.md)에서 관리합니다.

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