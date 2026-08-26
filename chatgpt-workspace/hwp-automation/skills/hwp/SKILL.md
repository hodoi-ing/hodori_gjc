---
name: hwp
description: HWP/HWPX 문서 작업을 인간형 무인(Zero-Touch) 방식으로 처리한다. "한글 문서 수정 / hwp 표 추가 / hwp 누름틀 채우기 / HWPX 생성 / 한글 보고서 자동화 / hwp 읽고 요약" 같은 요청에 활성화. 구형 HWP와 신형 HWPX를 바이트로 감별하고, 데이터 타입에 따라 XML 엔진(OS 무관) 또는 OLE 엔진(Windows+한글)으로 자동 라우팅하며, 결과를 스스로 검증한 뒤 원본을 보존한 _수정본을 산출한다.
---

# hwp — HWP/HWPX 문서 자동화 스킬 (Zero-Touch)

HWP 파일을 다루는 모든 요청은 이 스킬의 계약을 따른다.
세부 규격 문서는 저장소의 `chatgpt-workspace/hwp-automation/` 아래에 있다:
`ZERO_TOUCH_CHALLENGES.md`(장애물/해결 설계), `TEMPLATE_PROTOCOL.md`(양식 규칙), `hwp_bridge.py`(래퍼).

## 1. 도구 라우팅 (반드시 준수)

사용자 요청을 분석해 무기를 정한다.

| 작업 유형 | 예시 | 엔진 |
|---|---|---|
| 읽기 / 요약 / 분석 | "이 hwp 읽고 요약해 줘" | `syhwp` (순수 파서, OS 무관) |
| 텍스트·누름틀 치환 | "빈칸에 이름/날짜 채워줘" | `python-hwpx-automation` / `hwpx-kit` (XML) |
| 표 구조·서식 조작 | "표에 행 추가 / 셀 병합 / 색칠" | `pyhwpx` (OLE, Windows+한글 필수) |

- 입력 `str`/`dict` → XML 엔진. 입력 `list` → OLE 엔진. (계약: 절대 바꾸지 않는다)
- 구형 `.hwp`(바이너리)에 XML 치환은 **금지**. OLE 변환 후 진행하거나 에러를 보고한다.
- 형식 판별은 확장자가 아니라 바이트 시그니처(`D0 CF 11 E0`)로 한다.

## 2. 실행 프로토콜

1. `HWPBridge`를 써서 `_수정본` 복사본에서만 작업한다. 원본은 절대 덮어쓰지 않는다.
2. 의존성이 없어 막히면 즉시 에러를 보고하고, 설치 지침(`requirements.txt`)을 안내한다.
3. 작업 후 `verify_integrity()`로 스스로 검수한다:
   - HWPX: ZIP 무결성 + 미치환 필드(`{{...}}`) 잔여 검사
   - HWP(OLE): 재열기 검증이 없으면 `NotImplementedError`로 명시적 실패
   - 검증 실패 시 사람을 부르지 말고, 더 무거운 엔진(또는 변환 경로)으로 자동 재시도한다.
4. 완료 보고는 `IM_NOT_AI.md` 톤앤매너를 따른다. 로봇 어투 금지.

## 3. HWPX 자동화 비상 대응 (지옥의 5대 장애물)

- **팝업 무한 대기**: `SetMessageBoxMode` 억제 + `func-timeout`(60s) + `taskkill /f /im hwp.exe`
- **XML 표 붕괴**: 표 구조는 절대 XML로 직접 만지지 않는다. OLE엔진으로 라우팅
- **폰트 초기화**: `<hp:t>` 노드 삭제 금지, StyleID 상속 유지한 채 텍스트만 교체
- **멀티쓰레딩 충돌**: OLE 접근은 `filelock` 싱글톤 워커로 순차 처리
- **포맷 파편화**: 파이프라인 입구에서 HWP→HWPX 변환 후에만 메인 로직 실행