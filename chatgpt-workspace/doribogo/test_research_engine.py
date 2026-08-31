from research_engine import run_research


def test_three_loop_engine_stops_after_two_independent_links():
    calls = []

    def harvest(topic):
        calls.append(topic)
        return [
            {"title": f"{topic} official", "link": "https://example.com/official", "source": "official"},
            {"title": f"{topic} independent", "link": "https://example.com/independent", "source": "independent"},
        ]

    state = run_research("test topic", harvest=harvest, max_depth=2, max_steps=4)

    assert calls == ["test topic"]
    assert state.evidence
    assert any(d.get("reason") == "verified" for d in state.decisions if d.get("action") == "stop")


def test_engine_can_expand_when_initial_evidence_is_insufficient():
    calls = []

    def harvest(topic):
        calls.append(topic)
        if len(calls) == 1:
            return [{"title": "new branch", "link": "https://example.com/one", "source": "one"}]
        return [{"title": "second source", "link": "https://example.com/two", "source": "two"}]

    state = run_research("seed", harvest=harvest, max_depth=1, max_steps=3)

    assert len(calls) >= 2
    assert len(state.visited) >= 2
