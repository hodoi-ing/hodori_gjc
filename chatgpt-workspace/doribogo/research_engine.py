"""Three-loop generic autonomous research engine.

Loop 1: Discovery -> choose the next branch.
Loop 2: Harvest -> collect evidence from that branch.
Loop 3: Verify -> score evidence, discover new branches, or stop.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import importlib.util
from typing import Any, Callable, Iterable, Mapping

try:
    from .autonomous_discovery import DiscoveryCandidate, DiscoveryFrontier
except ImportError:
    _p=Path(__file__).resolve().parent/'autonomous_discovery.py'
    _s=importlib.util.spec_from_file_location('doribogo_autonomous_discovery',_p)
    _m=importlib.util.module_from_spec(_s); assert _s.loader is not None; _s.loader.exec_module(_m)
    DiscoveryCandidate, DiscoveryFrontier = _m.DiscoveryCandidate, _m.DiscoveryFrontier

@dataclass
class ResearchState:
    goal: str
    max_depth: int = 2
    max_steps: int = 6
    frontier: DiscoveryFrontier = field(init=False)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    visited: list[str] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    def __post_init__(self) -> None:
        self.frontier = DiscoveryFrontier(max_depth=self.max_depth, max_candidates=12)
        self.frontier.add(DiscoveryCandidate(self.goal,1.0,1.0,0.5,1.0,reason='initial research seed'))

def _normalize(rows: Iterable[Mapping[str, Any]] | None, topic: str) -> list[dict[str, Any]]:
    out=[]
    for row in rows or []:
        item=dict(row); item.setdefault('topic',topic)
        if item.get('title') or item.get('clean_title') or item.get('link'): out.append(item)
    return out

def verify_evidence(evidence: list[dict[str, Any]], *, core_question: str, min_sources: int=2):
    links={str(x.get('link','')) for x in evidence if x.get('link')}
    sources={str(x.get('source','')) for x in evidence if x.get('source')}
    titles={str(x.get('title',x.get('clean_title',''))) for x in evidence}
    score=min(1.0,(len(links)/max(min_sources,1))*0.5+(len(sources)/max(min_sources,1))*0.3+min(len(titles),4)*0.05)
    answered=len(evidence)>=min_sources and len(links)>=min_sources
    return answered,score,{'core_question':core_question,'unique_links':len(links),'unique_sources':len(sources),'unique_titles':len(titles),'verification_score':round(score,3)}

def _expand(evidence, parent, depth):
    return [DiscoveryCandidate(str(x.get('clean_title',x.get('title','')))[:160],0.65,0.7,0.55,0.7,depth,parent,'discovered from harvested evidence',{'source':x.get('source'),'link':x.get('link')}) for x in evidence if str(x.get('clean_title',x.get('title',''))).strip()]

def run_research(goal: str, *, harvest: Callable[[str],Iterable[Mapping[str,Any]]], max_depth:int=2, max_steps:int=6, min_sources:int=2, stop_threshold:float=0.25) -> ResearchState:
    state=ResearchState(goal,max_depth,max_steps)
    for step in range(max_steps):
        candidate=state.frontier.pop_next()
        if candidate is None: state.decisions.append({'step':step,'action':'stop','reason':'frontier_empty'}); break
        state.visited.append(candidate.topic)
        harvested=_normalize(harvest(candidate.topic),candidate.topic)
        state.evidence.extend(harvested)
        state.decisions.append({'step':step,'action':'harvest','topic':candidate.topic,'count':len(harvested),'depth':candidate.depth})
        answered,score,verification=verify_evidence(state.evidence,core_question=goal,min_sources=min_sources)
        state.decisions.append({'step':step,'action':'verify',**verification,'answered':answered})
        if answered and score>=stop_threshold:
            state.decisions.append({'step':step,'action':'stop','reason':'verified'}); break
        if candidate.depth<max_depth: state.frontier.extend(_expand(harvested[:4],candidate.topic,candidate.depth+1))
        if len(state.evidence)>=24: state.decisions.append({'step':step,'action':'stop','reason':'evidence_budget'}); break
    return state

def summarize_research(state: ResearchState)->dict[str,Any]:
    answered,score,verification=verify_evidence(state.evidence,core_question=state.goal)
    return {'goal':state.goal,'answered':answered,'verification_score':score,'verification':verification,'evidence':state.evidence,'visited':state.visited,'decisions':state.decisions,'research_path':state.frontier.history}

def run_doribogo_research(topic: str) -> dict[str, Any]:
    from doribogo_bot import harvest_5_way_radar
    return summarize_research(run_research(topic, harvest=harvest_5_way_radar))
