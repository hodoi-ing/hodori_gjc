# omg release v0.17.0 — 2026-07-14 게이트 증거

신규: `release-gate` 스킬 + `/omg:release`(3게이트 릴리스 세리머니, 10번째 스킬·15번째
커맨드) + **설치 시 sol 프리셋 자동 병합**(`merge_sol_preset`, 하코 지시 — 새 머신에서
/omg:presets 없이 CUSTOM 피커에 sol 즉시 노출) + 거버넌스 개정(게이트=에스컬레이션 장치,
데드엔드 금지 — 하코 지시 "게이트가 릴리스 자체를 막으면 안 된다").

## 1. 검증 게이트

| 항목 | 결과 |
|---|---|
| JSON/YAML 파스, 버전 3필드 0.17.0 일치, `bash -n` | OK |
| `bun test` | 117 pass / 0 fail (release-gate.test.ts·preset-merge.test.ts 신설 — fake gjc로 병합 5경로+실패 주입 3종 행동 검증) |
| 격리 HOME 신규 설치 repro (`/tmp/omg-repro-0170b`, 최종 후보 b5097f6) | rc=0 — 10 skills + 15 commands, `✓ preset (user): merged sol`, 병합본 planner=sol:high |
| 병합 3경로 실 gjc 검증 (신규 생성·추가·교체) + 롤백 실동작 | OK (교체: 타 프로파일·주석 무손상, 백업 생성) |

## 2. 외부 교차리뷰 게이트 — 2사이클

리뷰어: `GJC_NOTIFICATIONS=0 gjc -p --no-session --model openai-codex/gpt-5.6-sol:xhigh
--tools read,search,find`, 입력 = `git diff v0.16.0..HEAD` (시크릿 스캔 0건).

**사이클 1 (한도 소진 — 15건 지적, 전건 수정):**
- r1 (146d6a3): REQUEST_CHANGES 7건 — merge_sol_preset 비치명 위반(set -e 전파),
  병합 구조(후행 톱레벨 키·인라인 주석·내부 빈 줄·백업명 충돌), Gate3 사전 지시 우회,
  branch-flow 미준수 발행 경로, extragoal 계약 축약, metadata 카운트, 문자열-only 테스트.
- r2 (e99bfed): REQUEST_CHANGES 5건 — 원자성 잔여(mktemp 위치·cp 폴백·timeout 부재),
  인접 주석 경계, 빈도 예외 확장, **CRITICAL: 증거 문서 선커밋이 승인 HEAD 무효화**,
  플러그인 README 카운트.
- r3 (ed567c0): REQUEST_CHANGES 3건 — profiles 밖 `sol:` 오염 벡터, awk rc/cat 마스킹/
  OMG_PROBE_TIMEOUT=0/`timeout -k`, 트리 검사가 push 후 배치.
- **한도 소진 → 계약대로 발행 중단, 지적 전건 dev fix-forward(d0dca9a), 하코 에스컬레이션.**

**사이클 2 (하코 지시로 재개):**
- 초회 (b5097f6): **VERDICT: APPROVE** — "이전 사이클 15건은 모두 해소됐다. …
  에스컬레이션은 게이트 우회가 아니며 Gate 1·2와 자기 승인 금지 유지. 신규 릴리스 블로커 없음."

## 3. 승인 게이트 + 거버넌스 개정 기록

- 하코 세션 직접 지시: "오늘 발행하고 릴리즈 막는 것도 고쳐라" (2026-07-14) — 개정 계약의
  "기지시 릴리스 = G1·G2 통과 후 보고와 동시 발행" 경로로 발행.
- **빈도 캡 오버라이드 기록:** 당일 3번째 릴리스(v0.15.1·v0.16.0에 이어) — 하코 명시 지시.
- **거버넌스 개정(AGENTS.md §Release governance 4항):** 재서명 한도 소진=수정 후 운영자
  지시로 새 사이클, 빈도 초과=운영자 오버라이드, 기지시=보고와 동시 발행. 불변: G1·G2
  필수, 자기 승인 금지. 본 릴리스가 개정 절차의 첫 적용 사례(1사이클 중단→에스컬레이션→
  2사이클 재개→APPROVE→발행).

## 4. 발행

- 승인 HEAD `b5097f6` → main `--no-ff` 머지(`7dae8c0`) → **push 전 트리 검사**
  `git diff b5097f6..main --stat` = 0줄 확인 → 태그 `v0.17.0` → push → GitHub Release.
- 본 증거 문서는 개정 규칙대로 **발행 후 dev docs-only 커밋**(릴리스 태그 밖).
