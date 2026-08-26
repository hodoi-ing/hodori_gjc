# 🔒 hodori_gjc (호도리 전용 GJC 통합 안전 저장소)

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

<details>
<summary>🐯 도리보고 — 자세히 보기</summary>

### 🐯 도리보고 (Doribogo)

**위치:** `chatgpt-workspace/doribogo/`

> 요리보고 저리보고, 도리보고!

AI 생태계에서 최근 무슨 일이 벌어지고 있는지 여러 곳을 돌아다니며 찾아보고, 서로 다른 이슈를 카드별로 정리한 뒤 관련 사이트의 반응까지 한눈에 보여주는 조사 프로젝트입니다.

도리보고는 단순한 뉴스 요약기가 아닙니다. **주제 자체의 설명은 짧게 끝내고, 그 주제 안에서 최근 실제로 벌어진 서로 다른 변화·사건·논쟁·문제를 찾아내는 것**이 핵심입니다.

#### 🔀 두 가지 조사 모드

**🍳 DRT — 요리조리 보고와라!**  
Dori + Topic. 사용자가 주제를 정하면 그 대상을 요리조리 살펴봅니다.

`DRT → OpenCode Go → 최근 7일 → 5개`

**👀 DRI — 이슈보고 저리보고!**  
Dori + Issue. 특정 주제를 정하지 않고 여러 소스를 돌아다니며 최근 이슈를 찾아옵니다.

`DRI → AI → 오늘 → 5개`

| 모드 | 하는 일 |
|---|---|
| **DRT** | 내가 주제를 준다 → 도리보고가 조사한다 |
| **DRI** | 주제를 정하지 않는다 → 도리보고가 이슈를 찾아온다 |

#### 🃏 도리보고의 핵심

**카드 하나 = 서로 다른 이슈 하나**입니다.

예를 들어 OpenCode Go를 조사한다면 `새로운 모델 추가`, `사용량 변화`, `사용량 제한 논쟁`, `버그`, `가격 논쟁`처럼 서로 다른 이슈를 각각 하나의 카드로 만듭니다.

각 카드는 먼저 이슈를 이해할 수 있도록 설명하고, 그 아래에서 해당 이슈에 실제 의견이 확인된 사이트의 반응을 한줄평으로 보여줍니다.

```text
CARD
 ├─ 💡 이게 무슨 이슈야?
 ├─ 🔎 무슨 일이 벌어졌어?
 ├─ ❓ 왜 중요한데?
 ├─ 📌 확인된 사실
 ├─ 🌐 사이트별 한줄평
 ├─ ⚠️ 주의할 점 / 아직 모르는 것
 ├─ 👤 작성자 / 원문
 └─ 🔥 신호
```

모든 카드에 같은 내용을 반복하지 않으며, 이슈의 성격에 따라 필요한 설명을 다르게 구성합니다. 요청한 개수를 채우기 위해 의미 없는 이슈를 억지로 추가하지도 않습니다.

#### 🔍 어디서 찾아보지?

기본 후보는 X, Threads, Reddit, GitHub, GeekNews, OKKY, GPTers, 디스콰이엇, Velog, AI Hub 등입니다. 모든 주제에서 똑같은 사이트를 기계적으로 검색하는 것이 아니라 **이슈와 관련성이 높은 출처를 우선 확인하고 필요하면 공식 문서·뉴스·논문 등으로 교차검증**합니다.

#### ✏️ 이렇게 써요

도리보고의 결과는 초보 개발자도 바로 이해할 수 있게 씁니다. 전문용어는 처음 나왔을 때 쉬운 말로 풀고, 번역투와 로봇 같은 상투어를 피합니다. 저장소의 **`IM_NOT_AI.md`를 글쓰기 기준으로 참고**하며, 사실·작성자의 주장·도리보고의 해석을 구분합니다.

#### 📦 자료는 어떻게 보관해?

도리보고는 검색할 때마다 원문과 이미지 자료를 GitHub에 쌓지 않습니다. 현재는 **ChatGPT 웹 검색 → 여러 출처 조사 → 이슈 분류 → 반응 확인 → 카드뉴스형 텍스트 작성** 방식으로 MVP를 검증하고 있습니다.

출력 규격은 [`chatgpt-workspace/doribogo/CARD_FORMAT.md`](chatgpt-workspace/doribogo/CARD_FORMAT.md)에서 정의하며, **`IM_NOT_AI.md`를 1순위로 강제 적용**합니다. MVP 코드(`generated_code/trend_researcher.py`)도 이 규격에 맞춰 주제별 카드를 생성합니다.

상세 설계와 운영 기준은 [`chatgpt-workspace/doribogo/README.md`](chatgpt-workspace/doribogo/README.md)에서 관리합니다.

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
