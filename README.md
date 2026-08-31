# 🐯 hodori_gjc — 호도리 통합 프레임워크

> GJC를 중심으로 AI 자동화 프로젝트를 설계·검증·운영하는 비공개 통합 작업공간.

## 핵심 운영 규칙

- `PROTOCOL.md` — GJC와 ChatGPT의 공동 작업 규칙
- `ONTOLOGY.md` — 운영 방향, 판단 기준, 승인 원칙
- `IM_NOT_AI.md` — 문서/코드/리포트의 인간형 작성 규칙

## 주요 구성

### 🐯 도리보고
`chatgpt-workspace/doribogo/`

범용 Autonomous Research Engine을 목표로 한다.

```text
질문
 ↓
[1] Discovery
탐색 후보 생성 · 우선순위 · 깊이/예산 제한
 ↓
[2] Harvest
5-Way Radar · 뉴스/SNS/문서 등 증거 수집
 ↓
[3] Verification
출처 독립성 · 중복 제거 · 반대 증거 · 종료 판단
 ↓
최종 리서치
```

현재는 `autonomous_discovery.py`가 탐색 프론티어를 담당하고, `research_engine.py`가 세 루프를 연결한다. 기존 `doribogo_bot.py`의 5-Way Radar는 Harvest 계층으로 재사용한다.

### 📄 HWP/HWPX 자동화
`chatgpt-workspace/hwp-automation/`

- HWPX 읽기/추출
- placeholder/표 셀 내용 주입
- 표 구조 변경
- dry-run + 승인 게이트
- 원본 보존 + 수정본 생성
- 무결성/재열림 검증

구형 HWP는 직접 XML 수정하지 않고 **HWP → HWPX → 자동화 → 필요 시 HWP** 변환 계층으로 다루는 방향을 사용한다.

### 🦀 GJC 작업공간
`gjc-workspace/`

로컬 실행, 스크래핑, 테스트, 자동화에 필요한 실험 코드와 수집기를 둔다.

## 작업 원칙

1. 목적과 구조를 먼저 정한다.
2. 작은 변경 후 테스트한다.
3. 실제 데이터로 검증한다.
4. 안정화한 뒤 확장한다.
5. 핵심 구조 변경·삭제·비용·외부 공개는 승인 후 진행한다.

## 저장소 성격

이 저장소는 하나의 제품보다 **통합 프레임워크 + 연구/자동화 프로젝트 작업공간**에 가깝다. 완성된 기능과 실험 중인 기능을 같은 기준으로 보지 않고, 각 프로젝트의 구현/테스트/운영 단계를 별도로 관리한다.
