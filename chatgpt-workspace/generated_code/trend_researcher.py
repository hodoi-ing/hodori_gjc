"""Doribogo MVP: CARD_FORMAT.md 규격에 맞춘 리서치 카드 생성기.

입력: source/author/title/text/url 를 가진 JSON 레코드 목록.
출력: CARD_FORMAT.md(도리보고 2.0 출력 템플릿) 구조의 마크다운 카드 묶음.
      창의성(훅/앵글/인사이트)이 필요한 칸은 `<!-- LLM 작성 -->` 마커로 남겨
      작성 에이전트가 채울 수 있게 한다. 팩트·출처는 실제 데이터로 채운다.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

TOPICS = {
    "AI Agent": ["agent", "에이전트"],
    "AI Coding": ["codex", "claude code", "coding agent", "ai coding"],
    "MCP": ["mcp", "model context protocol"],
    "Local AI": ["local llm", "ollama", "qwen", "local ai"],
}


def detect_topic(text: str) -> str:
    lowered = text.lower()
    for topic, keywords in TOPICS.items():
        if any(keyword in lowered for keyword in keywords):
            return topic
    return "Other"


def load_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Input JSON must contain a list of records.")
    return data


def _llm_placeholder(label: str) -> str:
    """창의성 영역 표시: 작성 에이전트가 이 마커 자리에 글을 채운다."""
    return f"<!-- LLM 작성: {label} -->"


def build_cards(records: list[dict]) -> str:
    """주제별로 묶어 CARD_FORMAT.md 규격의 카드를 한 파일로 생성한다."""
    by_topic: dict[str, list[dict]] = {}
    for record in records:
        topic = record.get("topic") or detect_topic(
            f"{record.get('title', '')} {record.get('text', '')}"
        )
        by_topic.setdefault(topic, []).append(record)

    cards: list[str] = []
    for topic, group in sorted(by_topic.items()):
        sources = Counter(r.get("source", "unknown") for r in group)
        cards.append(build_one_card(topic, group, sources))
    return "\n\n---\n\n".join(cards) + "\n"


def build_one_card(topic: str, records: list[dict], sources: Counter) -> str:
    """주제 1개를 도리보고 2.0 카드 1장으로 변환한다."""
    source_line = ", ".join(f"{name} {count}건" for name, count in sources.most_common())

    fact_lines = []
    story_lines = []
    ref_lines = []
    for index, record in enumerate(records, start=1):
        title = record.get("title") or "제목 없음"
        author = record.get("author") or "작성자 미상"
        source = record.get("source", "unknown")
        text = (record.get("text") or "").strip()
        url = record.get("url")

        fact_lines.append(
            f"{index}. **{title}** — 작성자 **{author}** ({source})"
            + (f": {text}" if text else "")
        )
        story_lines.append(
            f"{index}. ({source} · {author}) _\"{text[:120]}\"_"
            if text
            else ""
        )
        ref_lines.append(
            f"- {url or '출처 URL 없음'} — {title} ({source} · {author})"
        )

    card = f"""# 📡 [DRI-{topic}] {_llm_placeholder('카드 타이틀 (매력적인 가제)')}

> 💡 **핵심 훅 (The Hook)**
> {_llm_placeholder('쌩초보도 클릭하게 만드는 한 줄 카피')}

| 🎯 콘텐츠 방향성 | 📊 트렌드 신선도 |
| :--- | :--- |
| **추천 포맷:** {_llm_placeholder('정보성 블로그 / 논란형 카드뉴스 / 기술 리뷰')} | **발생시점:** {_llm_placeholder('🔥방금 터짐 / 🟡확산 중 / 📉이미 기사화됨')} |
| **글쓰기 앵글:** {_llm_placeholder('비판적 관점 / 트렌드 전달 / 해결책 제시')} | **신뢰도:** 교차확인 {len(records)}건 ({source_line}) |

<br/>

### 1. 📝 콘텐츠 빌딩 블록 (글쓰기 재료)

* **📰 도입부 (초보자용 팩트 풀이):**
{chr(10).join('  * ' + line for line in fact_lines)}

* **🗣️ 스토리텔링 (대중의 반응):**
{chr(10).join('  * ' + line for line in story_lines if line)}

* **💡 차별화 인사이트 (전문가용 통찰):**
  * {_llm_placeholder('표면 아래 숨은 맥락 — 전문가가 감탄할 한 줄')}

### 2. 🔗 레퍼런스 소스 (원문 및 코드)

* **📰 대중 반응 / 기사:**
{chr(10).join('  ' + line for line in ref_lines)}

* **💬 킬러 인용구:** {_llm_placeholder('원문에서 뽑은 뼈때리는 명문장')}

### 3. ⚡ 콘텐츠 발행 자동화 연계

- [ ] **에이전트 인풋:** 본 카드의 팩트+반응+인사이트를 조합해 [워드프레스/인스타]용 초안 생성
- [ ] **자동화 연계 툴:** {_llm_placeholder('관련 오픈소스/라이브러리 추천')}
"""
    return card


def build_report(records: list[dict]) -> str:
    """과거 호환: 소스·주제별 집계 요약 (통계용)."""
    sources = Counter(record.get("source", "unknown") for record in records)
    topics = Counter(
        record.get("topic")
        or detect_topic(f"{record.get('title', '')} {record.get('text', '')}")
        for record in records
    )

    lines = [
        "# AI Trend Research Report",
        "",
        f"자료 수: {len(records)}",
        "",
        "## 출처별 자료 수",
        "",
    ]
    lines.extend(f"- {source}: {count}" for source, count in sources.most_common())
    lines += ["", "## 주제별 자료 수", ""]
    lines.extend(f"- {topic}: {count}" for topic, count in topics.most_common())
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("Usage: python trend_researcher.py <records.json> [--card|--summary]")
        return 2

    records = load_records(Path(sys.argv[1]))
    mode = sys.argv[2] if len(sys.argv) == 3 else "--card"
    if mode == "--summary":
        print(build_report(records))
    else:
        print("# 🐯 도리보고 리서치 카드 (CARD_FORMAT.md 규격)\n")
        print(build_cards(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())