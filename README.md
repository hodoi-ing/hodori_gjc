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
