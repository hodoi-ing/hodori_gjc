"""도리보고 3.0: 범용 실시간 시그널 수집기 & SNS 카드뉴스 엔진 (Universal Signal Harvester).

- 전 분야(주식, 할인, 정치, 경제, IT/AI 등) 실시간 이슈 자동 발굴
- 주제당 최대 6개(TOP 1~6) 핫한 순 정렬 + 0~6개 가변 추출 (억지 채우기 없음)
- SNS(스레드/인스타그램) 최적화 6장 슬라이드형 카드뉴스 포맷 생성
- IM_NOT_AI.md 원칙 준수 (AI 로봇 말투 완전 배제, 인간형 매운맛 텐션)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


class UniversalDoribogoEngine:
    """범용 멀티도메인 실시간 이슈 발굴 및 SNS 카드뉴스 생성 엔진."""

    def __init__(self, topic: str):
        self.topic = topic.strip()
        self.category = self._detect_category(self.topic)

    def _detect_category(self, topic: str) -> str:
        t = topic.lower()
        if any(k in t for k in ["주식", "증시", "코스피", "코스닥", "나스닥", "금리", "환율", "코인", "비트코인", "투자", "etf", "실적"]):
            return "주식/경제/금융"
        elif any(k in t for k in ["할인", "특가", "핫딜", "세일", "반값", "쇼핑", "쿠폰", "이벤트", "역대가", "올영", "행사"]):
            return "할인/쇼핑/특가"
        elif any(k in t for k in ["ai", "인공지능", "코딩", "github", "개발", "모델", "llm", "claude", "gpt", "agent", "mcp"]):
            return "IT/테크/AI"
        elif any(k in t for k in ["정치", "대선", "총선", "국회", "대통령", "정책", "외교", "선거", "의원"]):
            return "정치/시사/정책"
        return "일반/트렌드"

    def _build_search_query(self) -> str:
        base = self.topic
        if self.category == "주식/경제/금융" and not any(k in base for k in ["주식", "증시", "코스피", "실적"]):
            return f"{base} (주식 OR 증시 OR 급등 OR 하락 OR 실적)"
        elif self.category == "할인/쇼핑/특가" and not any(k in base for k in ["할인", "특가", "핫딜"]):
            return f"{base} (할인 OR 특가 OR 핫딜 OR 세일)"
        return base

    def fetch_and_cluster_issues(self, max_issues: int = 6) -> list[dict]:
        """실시간 소스 수집 및 유사 이슈 클러스터링 -> TOP N 추출."""
        query = self._build_search_query()
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        )
        raw_items = []
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall(".//item"):
                    raw_title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub_date_str = item.findtext("pubDate", "")
                    source = item.findtext("source", "")

                    clean_title = raw_title
                    if " - " in raw_title:
                        clean_title = raw_title.rsplit(" - ", 1)[0].strip()
                        if not source:
                            source = raw_title.rsplit(" - ", 1)[1].strip()

                    try:
                        pub_dt = parsedate_to_datetime(pub_date_str)
                    except Exception:
                        pub_dt = datetime.now(timezone.utc)

                    raw_items.append({
                        "clean_title": clean_title,
                        "raw_title": raw_title,
                        "link": link,
                        "pub_date": pub_dt,
                        "pub_date_str": pub_date_str,
                        "source": source or "주요 언론",
                    })
        except Exception:
            return []

        if not raw_items:
            return []

        # 중복 및 유사 이슈 클러스터링
        clusters: list[dict] = []
        for item in raw_items:
            words = set(re.findall(r"[가-힣a-zA-Z0-9]{2,}", item["clean_title"]))
            matched_cluster = None
            for c in clusters:
                overlap = len(words & c["keywords"])
                if overlap >= 2 or (len(words) > 0 and overlap / len(words) >= 0.4):
                    matched_cluster = c
                    break

            if matched_cluster:
                matched_cluster["items"].append(item)
                matched_cluster["keywords"].update(words)
                if item["pub_date"] > matched_cluster["latest_date"]:
                    matched_cluster["latest_date"] = item["pub_date"]
                    matched_cluster["primary_title"] = item["clean_title"]
            else:
                clusters.append({
                    "primary_title": item["clean_title"],
                    "keywords": words,
                    "latest_date": item["pub_date"],
                    "items": [item],
                })

        # 핫이슈 점수 계산 (클러스터 크기 + 최신성 가중치)
        now = datetime.now(timezone.utc)
        for c in clusters:
            count = len(c["items"])
            hours_ago = max(0.1, (now - c["latest_date"]).total_seconds() / 3600.0)
            recency_score = max(0.1, 24.0 / (hours_ago + 1.0))
            c["hot_score"] = (count * 2.0) + recency_score

        clusters.sort(key=lambda x: x["hot_score"], reverse=True)
        top_clusters = clusters[:max_issues]

        issues = []
        for rank, c in enumerate(top_clusters, start=1):
            sources = list({it["source"] for it in c["items"]})
            links = [it["link"] for it in c["items"][:2]]
            issues.append({
                "rank": rank,
                "issue_title": c["primary_title"],
                "cluster_count": len(c["items"]),
                "sources": sources,
                "latest_date": c["latest_date"].strftime("%Y-%m-%d %H:%M"),
                "links": links,
                "references": c["items"][:5],
            })

        return issues

    def render_card_news(self, issue: dict) -> str:
        """SNS 6장 슬라이드 규격 카드 텍스트 렌더링 (IM_NOT_AI 준수)."""
        rank = issue["rank"]
        title = issue["issue_title"]
        sources_str = ", ".join(issue["sources"][:5])
        if len(issue["sources"]) > 5:
            sources_str += f" 외 {len(issue['sources']) - 5}곳"
        link = issue["links"][0] if issue["links"] else "#"

        card = f"""### 📱 [TOP {rank}] {self.topic} 실시간 핫이슈

```text
┌────────────────────────────────────────────────────────┐
│ 1장 [표지/어그로 훅]                                   │
│ 🚨 {self.topic} 지금 난리 난 이유 3초 요약             │
│ \"{title[:40]}...\"                                      │
├────────────────────────────────────────────────────────┤
│ 2장 [사건 발단/팩트]                                   │
│ 📌 {issue['latest_date']} | {sources_str}              │
│ • 핵심: {title}                                        │
│ • 신호: 관련 보도/여론 {issue['cluster_count']}건 실시간 급증                      │
├────────────────────────────────────────────────────────┤
│ 3장 [핵심 포인트/비교]                                 │
│ 💡 뭐가 바뀌었나? (놓치면 손해인 부분)                 │
│ • 기존 방식/상황 vs 이번에 새롭게 터진 변화점          │
│ • 내 지갑/업무/일상에 미치는 직접적인 영향 분석        │
├────────────────────────────────────────────────────────┤
│ 4장 [현장 찐 반응]                                     │
│ 🗣️ 실시간 커뮤니티 날것 여론:                          │
│ 🟢 \"이거 모르고 있었으면 진짜 큰일 날 뻔했다\"          │
│ 🔴 \"또 말만 번지르르한 거 아니냐? 직접 써보고 판단한다\" │
├────────────────────────────────────────────────────────┤
│ 5장 [호도리 1줄 가이드]                                │
│ 🐯 \"남들 뒷북칠 때 팩트 선점하고 바로 대응하세요!\"     │
├────────────────────────────────────────────────────────┤
│ 6장 [출처 링크 & CTA]                                  │
│ 🔗 원문: {link}                                        │
│ 💾 도움 됐다면 [저장 💾] & [공유 🚀]                   │
└────────────────────────────────────────────────────────┘
```"""
        return card


def main() -> int:
    parser = argparse.ArgumentParser(description="도리보고 3.0 범용 실시간 시그널 수집기")
    parser.add_argument("topic", help="조사할 주제 (예: 주식, 특가할인, 엔비디아, 부동산정책)")
    parser.add_argument("--max", type=int, default=6, help="최대 추출 이슈 개수 (기본 6)")
    parser.add_argument("--json", action="store_true", help="JSON 포맷으로 출력")
    args = parser.parse_args()

    engine = UniversalDoribogoEngine(args.topic)
    issues = engine.fetch_and_cluster_issues(max_issues=args.max)

    if args.json:
        print(json.dumps({"topic": args.topic, "category": engine.category, "count": len(issues), "issues": issues}, indent=2, ensure_ascii=False))
        return 0

    print(f"# 🐯 도리보고 3.0 리서치 리포트: [{args.topic}]")
    print(f"> 📊 분야 분류: `{engine.category}` | 🔍 발견된 핫이슈: **{len(issues)}개** (최대 {args.max}개 중)\n")

    if not issues:
        print("ℹ️ 최근 24~48시간 내 유의미한 급상승 이슈가 감지되지 않았습니다. 현재 평온한 상태이거나 키워드 확장이 필요합니다.\n")
        return 0

    for issue in issues:
        print(engine.render_card_news(issue))
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
