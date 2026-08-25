"""Small MVP for grouping manually collected AI-trend signals.

Input: JSON list of records with source, title, text, and optional url/topic.
Output: Markdown summary with counts by source and topic.
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


def build_report(records: list[dict]) -> str:
    sources = Counter(record.get("source", "unknown") for record in records)
    topics = Counter(
        record.get("topic") or detect_topic(
            f"{record.get('title', '')} {record.get('text', '')}"
        )
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
    lines += ["", "## 원자료", ""]

    for index, record in enumerate(records, start=1):
        title = record.get("title") or "제목 없음"
        source = record.get("source", "unknown")
        url = record.get("url")
        suffix = f" — {url}" if url else ""
        lines.append(f"{index}. **{title}** ({source}){suffix}")

    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python trend_researcher.py <records.json>")
        return 2

    records = load_records(Path(sys.argv[1]))
    print(build_report(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
