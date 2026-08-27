"""Small regression tests for the DRI autonomous-discovery MVP."""

from autonomous_discovery import build_frontier, should_stop


def test_discovery_adds_new_candidate_and_skips_visited():
    observations = [
        {
            "depth": 0,
            "candidates": [
                {
                    "name": "OMP2",
                    "reason": "최근 Rust rewrite 확인",
                    "relevance": 0.9,
                    "novelty": 0.9,
                    "verification": 0.8,
                    "personal_value": 0.9,
                },
                {
                    "name": "Pi",
                    "reason": "이미 조사함",
                    "relevance": 0.9,
                    "novelty": 0.8,
                    "verification": 0.8,
                    "personal_value": 0.8,
                },
            ],
        }
    ]

    frontier = build_frontier(observations, visited={"Pi"})

    assert [candidate.name for candidate in frontier] == ["OMP2"]
    assert frontier[0].score > 0.0


def test_low_value_frontier_stops():
    observations = [
        {
            "depth": 0,
            "candidates": [
                {
                    "name": "noise",
                    "reason": "단순 언급",
                    "relevance": 0.1,
                    "novelty": 0.1,
                    "verification": 0.1,
                    "personal_value": 0.0,
                }
            ],
        }
    ]

    frontier = build_frontier(observations)

    assert should_stop(frontier) is True


def test_answered_question_with_two_sources_stops():
    assert should_stop(
        [], core_question_answered=True, independent_sources=2
    ) is True
