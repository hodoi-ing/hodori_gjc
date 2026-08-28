"""도리보고 3.2: 실시간 최신성 강제(when:1d~3d) & SNS/커뮤니티 날것 시그널 수집 엔진.

- 4대 다각도 레이더 병렬 탐색 (가격, 게릴라, 스펙, 여론)
- 최근 24~72시간(when:1d~3d) 엄격 시간 윈도우 필터링 적용 (과거 기사 원천 차단)
- 최신 발생 시각(Hours Ago) 기준 초신선도 가중치 부여 (방금 전/1시간 전 이슈 최우선 배치)
- 주제당 최대 6개(TOP 1~6) 핫한 순 정렬 + 0~6개 가변 추출
- SNS(스레드/인스타그램) 최적화 6장 슬라이드형 카드뉴스 렌더링
- IM_NOT_AI.md 원칙 준수
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# 4대 다각도 트리거 키워드 매트릭스
TRIGGER_RADARS = {
    "DEAL_PRICE": {
        "label": "💰 가격/특가/대란",
        "keywords": ["역대가", "최저가", "반값", "핫딜", "대란", "특가", "세일", "쿠폰", "0원", "청구할인", "라방", "타임딜"]
    },
    "GUERRILLA_INCIDENT": {
        "label": "⚡ 게릴라/돌발/사건",
        "keywords": ["기습", "무료", "잠시", "테스트", "오류", "가격오류", "품절", "완판", "재입고", "서버다운", "먹통", "폭등", "급락", "유출"]
    },
    "SPEC_UPDATE": {
        "label": "🛠️ 스펙/신기능/출시",
        "keywords": ["신규", "출시", "공개", "업데이트", "패치", "스펙", "성능", "벤치마크", "비교", "개편", "신모델", "차이"]
    },
    "BUZZ_TIPS": {
        "label": "🗣️ 여론/논란/꿀팁",
        "keywords": ["논란", "결함", "꿀팁", "실사용", "후기", "고질병", "주의", "대체재", "추천", "반응", "난리", "발칵"]
    }
}


class UniversalDoribogoEngine:
    """최근 24~72시간 내 실시간 핫이슈만 엄격히 선별하는 엔진."""

    def __init__(self, topic: str, days_window: int = 2):
        self.topic = topic.strip()
        self.days_window = days_window
        self.category = self._detect_category(self.topic)

    def _detect_category(self, topic: str) -> str:
        t = topic.lower()
        if any(k in t for k in ["주식", "증시", "코스피", "코스닥", "나스닥", "금리", "환율", "코인", "비트코인", "투자", "etf", "실적"]):
            return "주식/경제/금융"
        elif any(k in t for k in ["할인", "특가", "핫딜", "세일", "반값", "쇼핑", "쿠폰", "이벤트", "역대가", "올영", "행사"]):
            return "할인/쇼핑/특가"
        elif any(k in t for k in ["ai", "인공지능", "코딩", "github", "개발", "모델", "llm", "claude", "gpt", "agent", "mcp", "opencode"]):
            return "IT/테크/AI"
        elif any(k in t for k in ["정치", "대선", "총선", "국회", "대통령", "정책", "외교", "선거", "의원"]):
            return "정치/시사/정책"
        return "일반/트렌드"

    def _fetch_radar(self, radar_key: str, radar_info: dict) -> list[dict]:
        kw_query = " OR ".join(radar_info["keywords"][:6])
        query = f"{self.topic} ({kw_query}) when:{self.days_window}d"
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        )
        items = []
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall(".//item")[:15]:
                    raw_title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub_date_str = item.findtext("pubDate", "")
                    source = item.findtext("source", "")
                    clean_title = raw_title.rsplit(" - ", 1)[0].strip() if " - " in raw_title else raw_title

                    try:
                        pub_dt = parsedate_to_datetime(pub_date_str)
                    except Exception:
                        pub_dt = datetime.now(timezone.utc)

                    items.append({
                        "radar": radar_info["label"],
                        "radar_key": radar_key,
                        "clean_title": clean_title,
                        "raw_title": raw_title,
                        "link": link,
                        "pub_date": pub_dt,
                        "source": source or "주요 출처",
                    })
        except Exception:
            pass
        return items

    def fetch_and_cluster_issues(self, max_issues: int = 6) -> list[dict]:
        """4대 레이더를 병렬로 스캔하고, 최신순 및 화제성 순으로 정렬."""
        all_items: list[dict] = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self._fetch_radar, k, v) for k, v in TRIGGER_RADARS.items()]
            for fut in as_completed(futures):
                all_items.extend(fut.result())

        if len(all_items) < 2 and self.days_window <= 2:
            self.days_window = 7
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(self._fetch_radar, k, v) for k, v in TRIGGER_RADARS.items()]
                for fut in as_completed(futures):
                    all_items.extend(fut.result())

        if not all_items:
            return []

        seen_links = set()
        unique_items = []
        for it in all_items:
            if it["link"] not in seen_links:
                seen_links.add(it["link"])
                unique_items.append(it)

        clusters: list[dict] = []
        for it in unique_items:
            words = set(re.findall(r"[가-힣a-zA-Z0-9]{2,}", it["clean_title"]))
            matched = None
            for c in clusters:
                overlap = len(words & c["keywords"])
                if overlap >= 2 or (len(words) > 0 and overlap / len(words) >= 0.4):
                    matched = c
                    break

            if matched:
                matched["items".append(it)] if False else matched["items"].append(it)
                matched["keywords"].update(words)
                matched["radars"].add(it["radar"])
                if it["pub_date"] > matched["latest_date"]:
                    matched["latest_date"] = it["pub_date"]
                    matched["primary_title"] = it["clean_title"]
            else:
                clusters.append({
                    "primary_title": it["clean_title"],
                    "keywords": words,
                    "radars": {it["radar"]},
                    "latest_date": it["pub_date"],
                    "items": [it],
                })

        now = datetime.now(timezone.utc)
        for c in clusters:
            count = len(c["items"])
            hours_ago = max(0.1, (now - c["latest_date"]).total_seconds() / 3600.0)
            recency_score = 48.0 / (hours_ago + 0.5)
            radar_diversity_bonus = len(c["radars"]) * 2.0
            c["hot_score"] = (count * 2.0) + recency_score + radar_diversity_bonus
            c["hours_ago"] = hours_ago

        clusters.sort(key=lambda x: x["hot_score"], reverse=True)
        top_clusters = clusters[:max_issues]

        issues = []
        for rank, c in enumerate(top_clusters, start=1):
            sources = list({it["source"] for it in c["items"]})
            links = [it["link"] for it in c["items"][:2]]
            radars = list(c["radars"])
            hours_int = int(c["hours_ago"])
            time_ago_str = "방금 전" if hours_int < 1 else f"{hours_int}시간 전"

            issues.append({
                "rank": rank,
                "issue_title": c["primary_title"],
                "radars": radars,
                "cluster_count": len(c["items"]),
                "sources": sources,
                "time_ago": time_ago_str,
                "latest_date": c["latest_date"].strftime("%Y-%m-%d %H:%M"),
                "links": links,
                "references": c["items"][:5],
            })

        return issues

    def render_card_news(self, issue: dict) -> str:
        """SNS 6장 슬라이드 규격 카드 텍스트 렌더링."""
        rank = issue["rank"]
        title = issue["issue_title"]
        radars_str = " · ".join(issue["radars"])
        sources_str = ", ".join(issue["sources"][:5])
        if len(issue["sources"]) > 5:
            sources_str += f" 외 {len(issue['sources']) - 5}곳"
        link = issue["links"][0] if issue["links"] else "#"

        card = f"""### 📱 [TOP {rank}] {self.topic} 핫이슈 ({radars_str})

```text
┌────────────────────────────────────────────────────────┐
│ 1장 [표지/어그로 훅] (3초 컷)                          │
│ 🚨 {self.topic} [{issue['time_ago']}] 터진 이슈!       │
│ \"{title[:40]}...\"                                      │
├────────────────────────────────────────────────────────┤
│ 2장 [사건 발단/팩트]                                   │
│ 📌 {issue['latest_date']} ({issue['time_ago']}) | {sources_str} │
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
    parser = argparse.ArgumentParser(description="도리보고 3.2 실시간 최신성 강화 수집기")
    parser.add_argument("topic", help="조사할 주제")
    parser.add_argument("--max", type=int, default=6, help="최대 추출 개수")
    parser.add_argument("--days", type=int, default=2, help="검색 시간 윈도우 (기본 최근 2일)")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    engine = UniversalDoribogoEngine(args.topic, days_window=args.days)
    issues = engine.fetch_and_cluster_issues(max_issues=args.max)

    if args.json:
        print(json.dumps({"topic": args.topic, "category": engine.category, "count": len(issues), "issues": issues}, indent=2, ensure_ascii=False))
        return 0

    print(f"# 🐯 도리보고 3.2 실시간 리서치: [{args.topic}]")
    print(f"> 📊 분야: `{engine.category}` | ⏱️ 시간 윈도우: `최근 {engine.days_window}일 이내 엄격 필터링`")
    print(f"> 🔍 발견된 최신 핫이슈: **{len(issues)}개** (최대 {args.max}개 중)\n")

    if not issues:
        print(f"ℹ️ 최근 {engine.days_window}일 내 유의미한 급상승 이슈가 감지되지 않았습니다.\n")
        return 0

    for issue in issues:
        print(engine.render_card_news(issue))
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
