# 🔒 hodori_gjc

호도리 전용 GJC (Gajae Code) 비공개 저장소입니다.

## 📌 핵심 운영 규칙 (Single Source of Truth)

모든 AI 에이전트(GJC 하네스 및 ChatGPT 커넥터)는 글 작성, 코드 개발, 스크래핑, 프로젝트 진행 시 본 저장소의 다음 3대 규정을 필수적으로 읽고 준수해야 합니다.

1. **`ONTOLOGY.md`**: 호도리 온톨로지 및 AI 운영 센터 지침 (가치관, 우선순위, 위험도별 승인 규칙)
2. **`IM_NOT_AI.md`**: 인간형 글쓰기 및 AI 번역투/템플릿 제거 가이드
3. **`oh-my-gajae-code/`**: OMGC 멀티 에이전트 프레임워크 및 안전 운영 규칙

## 🛡️ 보안 규칙
1. API Key, SSH Key, 개인 토큰(`.env`, `mcp.json` 등)은 절대로 Git에 커밋하지 않습니다. (Pre-Commit Hook으로 자동 검사)
2. 모든 작업은 Private 상태를 유지합니다.
