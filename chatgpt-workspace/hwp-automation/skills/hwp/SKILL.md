---
name: hwp
description: HWP/HWPX 문서를 반자동화(내용은 자동, 구조는 승인 후) 방식으로 처리한다. "한글 문서 수정 / hwp 표 내용 채우기 / hwp 누름틀 채우기 / 여러 hwp 읽고 표에 정리 / 표 병합 / 행 추가 / HWPX 생성 / 한글 보고서 자동화 / hwp 읽고 요약" 같은 요청에 활성화. 로컬에 설치된 실동작 엔진(hwp_bridge.py)을 호출해 템플릿의 {{키}} 플레이스홀더를 값으로 채우고, 표 병합·행 추가 등 구조 변경은 dry-run으로 승인 근거를 보여준 뒤 사용자 승인을 받아 실행한다.
---

# hwp — HWPX 반자동화 스킬 (실동작, 전 기능 XML 기반)

이 스킬은 로컬에서 실제로 돌아가는 엔진을 호출한다.
핵심 원칙: **내용은 자동으로, 구조는 승인 후에.** Windows/OLE 없이 WSL2/Linux에서 전부 동작한다.

## 1. 실제 호출 방법 (GJC가 꼭 이대로 실행)

엔진 경로: `~/.gjc-free/hwp/hwp_bridge.py` 또는 `chatgpt-workspace/hwp-automation/hwp_bridge.py` (python3, 의존성 설치 완료)

```bash
# 1) 읽기/분석 (문단+표 구조를 JSON으로)
python3 hwp_bridge.py --read   문서.hwpx

# 2) 표 목록 확인 (tableIndex / 행·열 / 첫 행 프리뷰)
python3 hwp_bridge.py --tables 문서.hwpx

# 3) 내용 채우기 (표 셀·일반 문단의 {{키}} 를 값으로, 구조 불변)
python3 hwp_bridge.py --fill   문서.hwpx '{"user_name":"홍길동","date":"2026-08-26"}'

# 4) 구조 변경 계획 (dry-run, 승인 근거 transcript 출력 — 아직 실행 안 함)
python3 hwp_bridge.py --plan   문서.hwpx '[{"op":"merge_table","table_index":0}]'

# 5) 구조 변경 실행 (승인 후에만)
python3 hwp_bridge.py --apply  문서.hwpx '[{"op":"insert_row_by_clone","table_index":0,"ref_row":1,"count":1}]'
```

- 출력은 항상 `<원본>_수정본.hwpx`로 생성된다. **원본은 절대 안 바뀐다.**
- 템플릿에는 `{{키}}` 플레이스홀더를 넣어둔다. (표 셀·일반 문단 모두 `{{키}}` 문자 치환)

## 2. 지원 구조 변경 op (apply_table_ops)

| op | 설명 |
|---|---|
| `merge_table` | `table_index` 표를 바로 다음 표와 병합 (colCnt 불일치/중간 텍스트 있으면 거부) |
| `insert_row_by_clone` | `ref_row` 뒤에 `count`행 복제 추가 (서식 상속) |
| `insert_block_by_clone` | 세로 병합 블록(`ref_rows:[r0,r1]`)을 `count`회 복제 |
| `split_table` | `split_row` 기준으로 표를 둘로 분리 |
| `delete_row` / `delete_column` | 행/열 삭제 |
| `delete_table` | 표 삭제 |

## 3. 운영 규칙 (내용 자동 / 구조 승인)

1. **내용 주입**: `--fill`은 표 셀(`fill_cells`)과 일반 문단(`paragraph_patch`)의 텍스트만 바꾼다.
   행·열·병합·위치 같은 기하 구조는 절대 안 바뀐다.
2. **구조 변경 승인 게이트**: 구조 변경이 필요하면 `--plan`(dry-run)으로 [op/dims 전후/승인 근거]를 보여주고
   사용자에게 "진행할까요?"를 물은 뒤, 승인을 받아야 `--apply`로 실행한다.
3. 거부 시 계획을 폐기하고 문서는 무변경이다. 내용만으로 가능한 대안을 제안한다.

## 4. 비상 대응 (기술 장애물)

- 표 구조는 반드시 `--apply`(apply_table_ops)로만 바꾼다. XML을 손으로 직접 편집하지 않는다.
- 중첩 표(표 안의 표)는 구조 변경 불가 → 실패 시 정직하게 보고한다.
- 구형 `.hwp`(바이너리, `D0 CF 11 E0`)는 XML 치환 불가 → 먼저 `.hwpx`로 변환 필요.

## 5. 관련 문서

- `SEMI_AUTOMATION.md` — 반자동화 운영 규약 (승인 게이트)
- `ZERO_TOUCH_CHALLENGES.md` — 자동 구간 기술 장애물
- `TEMPLATE_PROTOCOL.md` — 템플릿 작성 규칙
- `hwp_bridge.py` — 실동작 엔진 (CLI)