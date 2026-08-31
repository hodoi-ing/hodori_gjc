"""Generic autonomous research frontier and discovery loop.

The discovery layer is domain-agnostic. It does not use personal-value scoring
or hard-coded news topics; it decides which research branches are worth pursuing
and when the search should stop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


@dataclass
class DiscoveryCandidate:
    topic: str
    relevance: float = 0.0
    novelty: float = 0.0
    verification: float = 0.0
    information_gain: float = 0.0
    depth: int = 0
    parent: str | None = None
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def research_value(self) -> float:
        return (self.relevance + self.novelty + self.verification + self.information_gain) / 4

    @property
    def score(self) -> float:
        return self.research_value

    @property
    def name(self) -> str:
        return self.topic


class DiscoveryFrontier:
    """Priority queue for promising research branches."""

    def __init__(self, *, max_depth: int = 3, max_candidates: int = 10) -> None:
        self.max_depth = max_depth
        self.max_candidates = max_candidates
        self._candidates: list[DiscoveryCandidate] = []
        self.visited: set[str] = set()
        self.history: list[dict[str, Any]] = []

    def add(self, candidate: DiscoveryCandidate) -> bool:
        topic = candidate.topic.strip()
        if not topic or candidate.depth > self.max_depth or topic in self.visited:
            return False
        candidate.topic = topic
        self._candidates.append(candidate)
        self._candidates.sort(key=lambda item: item.research_value, reverse=True)
        self._candidates = self._candidates[: self.max_candidates]
        return True

    def extend(self, candidates: Iterable[DiscoveryCandidate]) -> None:
        for candidate in candidates:
            self.add(candidate)

    def pop_next(self) -> DiscoveryCandidate | None:
        while self._candidates:
            candidate = self._candidates.pop(0)
            if candidate.topic in self.visited:
                continue
            self.visited.add(candidate.topic)
            self.history.append({
                "topic": candidate.topic,
                "parent": candidate.parent,
                "reason": candidate.reason,
                "research_value": candidate.research_value,
                "depth": candidate.depth,
            })
            return candidate
        return None

    def should_continue(self, *, expected_information_gain: float, threshold: float = 0.25) -> bool:
        return bool(self._candidates) and expected_information_gain >= threshold

    def __len__(self) -> int:
        return len(self._candidates)


def _candidate_from_mapping(
    data: Mapping[str, Any], depth: int = 0, parent: str | None = None
) -> DiscoveryCandidate:
    return DiscoveryCandidate(
        topic=str(data.get("name", data.get("topic", ""))).strip(),
        relevance=float(data.get("relevance", 0.0)),
        novelty=float(data.get("novelty", 0.0)),
        verification=float(data.get("verification", 0.0)),
        information_gain=float(data.get("information_gain", data.get("personal_value", 0.0))),
        depth=int(data.get("depth", depth)),
        parent=data.get("parent", parent),
        reason=str(data.get("reason", "")),
        metadata=dict(data.get("metadata", {})),
    )


def build_frontier(
    observations: Iterable[Mapping[str, Any]],
    visited: set[str] | None = None,
    *,
    max_depth: int = 3,
    max_candidates: int = 10,
) -> list[DiscoveryCandidate]:
    """Build the next frontier from observed candidates."""
    frontier = DiscoveryFrontier(max_depth=max_depth, max_candidates=max_candidates)
    frontier.visited = set(visited or set())
    for observation in observations:
        depth = int(observation.get("depth", 0))
        for raw in observation.get("candidates", []):
            candidate = _candidate_from_mapping(raw, depth=depth)
            frontier.add(candidate)
    return list(frontier._candidates)


def should_stop(
    frontier: Iterable[DiscoveryCandidate],
    *,
    core_question_answered: bool = False,
    independent_sources: int = 0,
    min_research_value: float = 0.25,
) -> bool:
    """Stop when the question is adequately supported or no worthwhile branch remains."""
    candidates = list(frontier)
    if core_question_answered and independent_sources >= 2:
        return True
    if not candidates:
        return True
    return max(candidate.research_value for candidate in candidates) < min_research_value


def propose_candidates(
    discoveries: Iterable[Mapping[str, Any]], *, depth: int, parent: str
) -> list[DiscoveryCandidate]:
    """Convert newly discovered entities into candidates for the next loop."""
    return [
        candidate
        for candidate in (
            _candidate_from_mapping(item, depth=depth, parent=parent)
            for item in discoveries
        )
        if candidate.topic
    ]
