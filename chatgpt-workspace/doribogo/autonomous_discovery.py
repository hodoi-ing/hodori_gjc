"""Generic autonomous research frontier for Doribogo.

This module intentionally contains no user-personal relevance scoring.
It decides which newly discovered research candidates are worth pursuing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class DiscoveryCandidate:
    topic: str
    relevance: float
    novelty: float
    verification: float
    information_gain: float
    depth: int = 0
    parent: str | None = None
    reason: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def research_value(self) -> float:
        values = (
            self.relevance,
            self.novelty,
            self.verification,
            self.information_gain,
        )
        return sum(values) / len(values)


class DiscoveryFrontier:
    """Keep promising research branches while preventing unbounded expansion."""

    def __init__(self, *, max_depth: int = 3, max_candidates: int = 10) -> None:
        self.max_depth = max_depth
        self.max_candidates = max_candidates
        self._candidates: list[DiscoveryCandidate] = []
        self.history: list[dict] = []

    def add(self, candidate: DiscoveryCandidate) -> bool:
        if candidate.depth > self.max_depth:
            return False
        self._candidates.append(candidate)
        self._candidates.sort(key=lambda item: item.research_value, reverse=True)
        self._candidates = self._candidates[: self.max_candidates]
        return True

    def extend(self, candidates: Iterable[DiscoveryCandidate]) -> None:
        for candidate in candidates:
            self.add(candidate)

    def pop_next(self) -> DiscoveryCandidate | None:
        if not self._candidates:
            return None
        candidate = self._candidates.pop(0)
        self.history.append(
            {
                "topic": candidate.topic,
                "parent": candidate.parent,
                "reason": candidate.reason,
                "research_value": candidate.research_value,
                "depth": candidate.depth,
            }
        )
        return candidate

    def should_continue(self, *, expected_information_gain: float, threshold: float = 0.25) -> bool:
        return bool(self._candidates) and expected_information_gain >= threshold

    def __len__(self) -> int:
        return len(self._candidates)
