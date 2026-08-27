# 📜 도리보고 (Doribogo) 변경 이력 & 버전 기록

> 도리보고 프로젝트의 버전별 주요 업데이트 내역과 시스템 변경 사항을 기록합니다.

---

## 🧠 [v2.6.0] - 2026-08-27 (Notion MCP Integration & Knowledge Base Auto-Sync)

### 🆕 주요 신규 기능 (New Features)
- **Notion MCP 연동 및 자동 동기화 구축:**
  - `~/.gjc-free/mcp.json` 내 `notion-mcp-server` 검증 및 API 연동 완료.
  - 리서치 결과를 Notion `🧬 개인 AI 마스터 DB` (`fc476391-66f1-4ce9-88c6-49b232ffbac1`) 및 `[호도리저장소]` (`3c8401c8-bc0f-8147-b36b-db4ca9c13b29`) 페이지로 자동 동기화할 수 있는 수집/발행 파이프라인 추가.
  - `RADAR.md` 내 노션 데이터베이스 속성 필드 맵핑(이름, AI요약, AI해석, 출처, 분류, 중요도, 자동화가능성 등) 명시.

---
## 🚀 [v2.5.0] - 2026-08-27 (Autonomous Pipeline & Thread-Style Editorial Release)

### 🆕 주요 신규 기능 (New Features)
- **5단계 자율 탐색 파이프라인 (Autonomous Search Pipeline) 탑재:**
  - `다각도 병렬 데이터 수집 ➔ insane_search WAF 우회 & 마크다운 본문 추출 ➔ autonomous_discovery 가치 평가 ➔ 3단계 교차 검증 ➔ 렌더링` 자율 탐색 룹 구축.
- **스레드(Threads) 특화 톤앤매너 시스템 탑재 (`CARD_FORMAT.md` v2.0):**
  - 단순 요약을 벗어나 `공감 훅(Hook) + 도입부 팩트 + 찐광기 현장 반응(Storytelling) + 전문가용 차별화 인사이트` 4단계 구조화.
  - `IM_NOT_AI.md` 원칙에 기반한 매운맛 텐션 강제 적용.
- **GJC Native Skill 자동화 패키징:**
  - `.gjc/skills/doribogo/SKILL.md` 스킬 정의 추가 (`/skill:doribogo` 명령어로 무인 리서치 실행 지원).

### 🎯 레이더 및 소스 확장 (Radar Updates)
- `RADAR.md` 내 최신 테크 인플루언서 계정 `@junyoung.ai` 감시 목록 반영.
- GitHub 발견 레이더(Trending / Stars 20만+ 레포지토리 및 실시간 릴리스 패치) 연동 강화.

---

## 🛠️ [v2.0.0] - 2026-08-20 (Doribogo 2.0 Core Architecture)

### 📌 구조 변경 (Architecture Changes)
- **투트랙 탐색 시스템 정립:**
  - `DRT` (Dori + Topic: 사용자 지정 주제 심층 탐색)
  - `DRI` (Dori + Issue: 자율 이슈 발굴 + GitHub 급상승 프로젝트 필수 캡처)
- **AI 봇 문체 금지 지침 (`IM_NOT_AI.md`) 적용:**
  - 상투적 번역투 및 "현대 디지털 시대에", "결론적으로" 식의 앵무새 문체 엄격 금지.

---

## 🌱 [v1.0.0] - 2026-08-10 (MVP Initial Release)
- 기본 뉴스 스크래핑 및 카드뉴스 텍스트 렌더링 MVP 검증.
- Naver 뉴스/블로그 크롤러 및 기본 수집 스크립트 작성.
