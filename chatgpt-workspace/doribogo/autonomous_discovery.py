"""DRI autonomous-discovery MVP.

이 모듈은 웹 검색을 수행하지 않는다.
조사 결과에서 발견된 후보를 frontier로 관리하고, 다음에 무엇을 조사할지
작은 예산 안에서 결정하는 순수 로직만 담당한다.

입력 예시:
{
  "goal": "오늘 AI 개발 생태계의 중요한 변화",
  "observations": [
    {
      "source": "github",
      "title": "OMP2",
      "text": "Rust rewrite of Pi...",
      "candidates": [
        {"name": "Pi", "reason": "OMP2의 기반과 관계를 확인할 필요가 있음"}
      ]
    }
  ]
}

출력은 다음 탐색 후보와 종료 판단을 JSON으로 반환한다.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Candidate:
    """다음 탐색 대상으로 고려할 항목."""

    name: str
    reason: str
    relevance: float = 0.0
    novelty: float = 0.0
    verification: float = 0.0
    personal_value: float = 0.0
    depth: int = 0

    @property
    def score(self) -> float:
        """탐색 우선순위. 설명 가능한 고정 가중치를 사용한다."""
        return round(
            self.relevance * 0.35
            + self.novelty * 0.25
            + self.verification * 0.20
            + self.personal_value * 0.20,
            4,
        )


def normalize(value: str) -> str:
    """중복 후보 제거를 위한 간단한 정규화."""
    return re.sub(r"\s+", " ", value.strip().lower())


def candidate_from_record(record: dict, depth: int) -> Candidate | None:
    """LLM/검색 계층이 만든 후보 레코드를 안전하게 Candidate로 변환한다."""
    name = str(record.get("name", "")).strip()
    reason = str(record.get("reason", "")).strip()
    if not name or not reason:
        return None

    def score(name: str) -> float:
        try:
            return max(0.0, min(1.0, float(record.get(name, 0.0))))
        except (TypeError, ValueError):
            return 0.0

    return Candidate(
        name=name,
        reason=reason,
        relevance=score("relevance"),
        novelty=score("novelty"),
        verification=score("verification"),
        personal_value=score("personal_value"),
        depth=depth,
    )


def build_frontier(
    observations: list[dict],
    *,
    visited: set[str] | None = None,
    max_depth: int = 2,
    max_candidates: int = 5,
) -> list[Candidate]:
    """관찰 결과에서 다음 탐색 frontier를 만든다."""
    visited_keys = {normalize(item) for item in (visited or set())}
    unique: dict[str, Candidate] = {}

    for observation in observations:
        depth = int(observation.get("depth", 0)) + 1
        if depth > max_depth:
            continue

        for raw in observation.get("candidates", []):
            candidate = candidate_from_record(raw, depth)
            if candidate is None:
                continue
            key = normalize(candidate.name)
            if key in visited_keys:
                continue
            previous = unique.get(key)
            if previous is None or candidate.score > previous.score:
                unique[key] = candidate

    return sorted(
        unique.values(),
        key=lambda item: (-item.score, item.depth, normalize(item.name)),
    )[:max_candidates]


def should_stop(
    frontier: list[Candidate],
    *,
    core_question_answered: bool = False,
    independent_sources: int = 0,
    min_independent_sources: int = 2,
    minimum_score: float = 0.45,
) -> bool:
    """추가 탐색 가치가 충분하지 않으면 True."""
    if core_question_answered and independent_sources >= min_independent_sources:
        return True
    return not any(candidate.score >= minimum_score for candidate in frontier)


def load_input(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Input JSON must contain an object.")
    return data


def run(data: dict) -> dict:
    """탐색 상태의 다음 frontier와 종료 판단을 반환한다."""
    budget = data.get("budget", {})
    max_depth = int(budget.get("max_depth", 2))
    max_candidates = int(budget.get("max_candidates", 5))
    visited = set(data.get("visited", []))
    observations = data.get("observations", [])

    frontier = build_frontier(
        observations,
        visited=visited,
        max_depth=max_depth,
        max_candidates=max_candidates,
    )

    independent_sources = int(data.get("independent_sources", 0))
    core_question_answered = bool(data.get("core_question_answered", False))

    return {
        "goal": data.get("goal", ""),
        "frontier": [
            {**asdict(candidate), "score": candidate.score} for candidate in frontier
        ],
        "stop": should_stop(
            frontier,
            core_question_answered=core_question_answered,
            independent_sources=independent_sources,
        ),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python autonomous_discovery.py <state.json>")
        return 2

    result = run(load_input(Path(sys.argv[1])))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
