# 📄 HWP/HWPX 자동화

> HWP/HWPX 문서를 AI Agent가 안전하게 읽고, 내용과 표 구조를 자동화하는 반자동화 파이프라인.

## 현재 구현 상태

### ✅ HWPX 코어 엔진

`hwp_bridge.py`가 실제 실행 가능한 CLI 브리지로 동작한다.

```bash
python3 hwp_bridge.py --read   문서.hwpx
python3 hwp_bridge.py --fill   문서.hwpx '{"이름":"홍길동"}'
python3 hwp_bridge.py --verify 문서.hwpx
python3 hwp_bridge.py --tables 문서.hwpx
python3 hwp_bridge.py --plan   문서.hwpx '[{"op":"insert_row_by_clone","table_index":0,"ref_row":1,"count":1}]'
python3 hwp_bridge.py --apply  문서.hwpx '[{"op":"insert_row_by_clone","table_index":0,"ref_row":1,"count":1}]'
```

현재 구현된 기능:

- HWP/HWPX 형식 감지
- HWPX 문단/표 내용 추출
- `{{키}}` 플레이스홀더 치환
- 표 셀 직접 채우기
- 원본 보존 + `<원본>_수정본.hwpx` 생성
- 반복 실행 시 항상 원본 템플릿에서 다시 시작
- 문서 재열림 안전성 검증
- 미치환 placeholder 검증
- 표 조회
- 표 행 추가/삭제
- 표 병합/분리
- 구조 변경 dry-run transcript 생성
- 승인되지 않은 구조 변경 실행 차단

### 사용 엔진

- `python-hwpx-automation`: 내용 패치, 텍스트 추출, 검증
- `syhwp`: 보조 파서
- `pyhwpx`: Windows + 한글 설치 환경에서 필요한 고급 HWP 조작의 보조 수단

## HWP 입력을 어떻게 처리할 것인가?

구형 `.hwp`는 바이너리 OLE 문서라 현재 XML 기반 엔진으로 직접 안전하게 구조 변경하기 어렵다. 따라서 **HWP → HWPX 변환 → 자동화 → 필요 시 HWP 재변환** 전략은 현실적인 방향이다.

다만 변환을 무조건 거치는 것은 권장하지 않는다. 변환 과정에서 다음이 달라질 수 있기 때문이다.

- 일부 레이아웃/개체 호환성
- 글꼴/간격/필드 표현
- 특수 개체 및 매크로성 요소
- 한글 버전별 저장 결과

### 권장 정책

```text
입력 문서
  │
  ├─ HWPX ───────────────► HWPX 엔진 직접 처리
  │
  └─ HWP
       │
       ▼
   HWP → HWPX 변환
       │
       ▼
   HWPX 자동화
       │
       ▼
   검증
       │
       ├─ 사용자가 HWPX 결과를 받을 수 있으면 그대로 반환
       │
       └─ 반드시 HWP가 필요한 경우
              ▼
          HWPX → HWP 변환
              ▼
          재검증 후 반환
```

핵심은 **내부 작업 포맷은 HWPX로 통일하고, HWP는 입출력 호환 계층으로 취급하는 것**이다.

### 변환 계층 권장안

1. Windows + 한글 설치 환경에서는 한글/pyhwpx 기반 변환을 우선한다.
2. 변환 결과는 원본과 별도 작업 디렉터리에 둔다.
3. 변환 직후 HWPX 구조 검사를 한다.
4. 자동화 후 다시 HWP로 변환했다면 최종 HWP도 열림/구조 검증을 거친다.
5. 변환 자체가 불안정한 문서는 fail-closed로 중단하고 원본을 건드리지 않는다.

## 안전 원칙

- 원본 절대 덮어쓰기 금지
- 내용 변경은 자동화 가능
- 표/문서 구조 변경은 승인 후 실행
- 변환 실패 시 원본 반환
- 검증 실패 시 결과물 폐기

## 현재 남은 과제

- 실제 HWP↔HWPX 변환 브리지 표준화
- 변환 후 레이아웃 회귀 테스트
- 실제 샘플 문서 묶음으로 end-to-end 검증
- 중첩 표 등 fail-closed 영역 확대 검증
