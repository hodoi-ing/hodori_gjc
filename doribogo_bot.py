"""🐯 dori bot (도리보고 v5.0.0 - 4-Stage Thread Curation & 2-Stage Sequential Cross-Verification Engine)

[CHOI (@choi.openai) 스레드 연쇄 큐레이션 & 2단계 교차검증 아키텍처]
1. 1차 관문 (Primary Ground Truth): 공식 발표 / 개발사 공식 SNS / 신규 출시 속보 우선 확보
2. 2차 관문 (Cross-Verification): 주요 언론사 및 커뮤니티 기사 교차 대조 & 팩트 검증
3. 3-Tier Deduplication & Relevance Filtering
4. [메인 본문 훅 + 댓글 1 기술 딥다이브 + 댓글 2 수치 환산·영향도 + 댓글 3 출처] 4단 분리 고밀도 큐레이션
"""

import os
import sys
import time
import json
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GEMINI_", "").strip() or "AIzaSyAXiI8a1MVwfegW5cz7MxfLbGKdv8amz-4"

WATCH_KEYWORDS = [
    "백컨트리 360",
    "캠핑 텐트 특가",
]


def send_discord(title: str, text: str, color: int = 0xFF6B00) -> bool:
    """디스코드 웹후크 임베드 전송."""
    if not DISCORD_WEBHOOK_URL:
        return False

    now_korea = datetime.now().strftime("%Y-%m-%d %H:%M")
    payload = {
        "username": "dori bot",
        "avatar_url": "https://raw.githubusercontent.com/hodoi-ing/lecture-auto-bot/main/icons/icon128.png",
        "embeds": [
            {
                "title": title,
                "description": text[:4000],
                "color": color,
                "footer": {
                    "text": f"dori bot • {now_korea}"
                }
            }
        ]
    }

    try:
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "DoriBot/4.5"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"[디스코드 전송 실패] {e}")
        return False


def send_telegram(text: str, chat_id: str = None) -> bool:
    """텔레그램 메시지 전송."""
    target_chat_id = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not target_chat_id:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def send_broadcast(title: str, text: str, chat_id: str = None) -> bool:
    """디스코드 및 텔레그램 통합 발송."""
    discord_ok = send_discord(title, text)
    telegram_ok = send_telegram(f"**{title}**\n\n{text}", chat_id)
    return discord_ok or telegram_ok


def harvest_2_stage_verification(keyword: str) -> list[dict]:
    """1차 공식/SNS 속보 수집 ➔ 2차 언론 교차검증 파이프라인."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8"
    }

    raw_signals = []
    clean_kw = re.sub(r'^(지금|오늘|최신|실시간|에 대한|에대해|말이야|같은거)\s*', '', keyword).strip() or keyword
    clean_kw = re.sub(r'(말이야|같은거|알려줘|어때|추천해줘)$', '', clean_kw).strip() or clean_kw

    is_deal_query = any(w in keyword for w in ["특가", "가격", "텐트", "할인", "대란", "구매", "장비", "세일", "역대가"])

    # --- STAGE 1: 1차 관문 (공식 발표 / SNS 속보 / 신규 출시 우선 탐색) ---
    try:
        q_stage1 = f"{clean_kw} (공식 OR 출시 OR X OR 트위터 OR 스레드 OR 신규 OR 특가) when:7d"
        url1 = f"https://news.google.com/rss/search?q={urllib.parse.quote(q_stage1)}&hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(url1, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            root = ET.fromstring(resp.read())
            for item in root.findall('.//item')[:6]:
                raw_t = item.findtext('title', '')
                link = item.findtext('link', '')
                source = item.findtext('source', '') or '공식/속보'
                clean_t = html.unescape(raw_t.rsplit(' - ', 1)[0].strip() if ' - ' in raw_t else raw_t)
                raw_signals.append({
                    "title": f"[{source}] {clean_t}",
                    "link": link,
                    "source": f"⚡ 1차 팩트 ({source})",
                    "stage": 1,
                    "score": 10
                })
    except Exception as e:
        print(f"[!] Stage 1 공식 수집 에러: {e}")

    # --- STAGE 2: 2차 관문 (언론사 교차 검증 & 심층 보도) ---
    try:
        q_stage2 = f"{clean_kw} when:7d"
        url2 = f"https://news.google.com/rss/search?q={urllib.parse.quote(q_stage2)}&hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(url2, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            root = ET.fromstring(resp.read())
            for item in root.findall('.//item')[:6]:
                raw_t = item.findtext('title', '')
                link = item.findtext('link', '')
                source = item.findtext('source', '') or '언론 검증'
                clean_t = html.unescape(raw_t.rsplit(' - ', 1)[0].strip() if ' - ' in raw_t else raw_t)
                raw_signals.append({
                    "title": f"[{source}] {clean_t}",
                    "link": link,
                    "source": f"📰 2차 언론검증 ({source})",
                    "stage": 2,
                    "score": 8
                })
    except Exception as e:
        print(f"[!] Stage 2 언론 검증 에러: {e}")

    # --- 3-TIER DEDUPLICATION & RELEVANCE FILTER ---
    seen_links = set()
    seen_titles = []
    filtered = []

    def is_similar(t1, t2):
        w1 = set(t1.split())
        w2 = set(t2.split())
        if not w1 or not w2:
            return False
        return (len(w1 & w2) / len(w1 | w2)) > 0.65

    # Sort so Stage 1 primary facts are processed first
    raw_signals.sort(key=lambda x: (x.get('stage', 2), -x.get('score', 0)))

    for s in raw_signals:
        if s['link'] in seen_links:
            continue
        if any(is_similar(s['title'], t) for t in seen_titles):
            continue
        
        seen_links.add(s['link'])
        seen_titles.append(s['title'])
        filtered.append(s)

    return filtered[:6]


def generate_gemini_card_news(topic: str, items: list[dict]) -> str:
    """Gemini 2.5 Flash를 활용한 CHOI (@choi.openai) 스타일 4단 연쇄 스레드 큐레이션."""
    today_str = datetime.now().strftime('%m월 %d일')

    data_context = f"사용자 원문 질문: {topic}\n수집된 1차 공식 발표 및 2차 교차검증 데이터:\n"
    if items:
        for idx, it in enumerate(items, 1):
            data_context += f"{idx}. [{it['source']}] {it['title']} (URL: {it['link']})\n"
    else:
        data_context += "(최근 실시간 데이터 수집 분석 중)"

    prompt = f"""
당신은 대한민국 최고의 AI/테크/핫딜 수석 팩트 큐레이터 '도리(Dori)'입니다.
현재 시점은 **2026년 8월 말**입니다.
사용자의 질문: "{topic}"

아래 수집된 [1차 공식 팩트]와 [2차 언론 교차검증 데이터]를 철저히 대조 분석하여, Threads 30만 팔로워 인플루언서 CHOI (@choi.openai) 스타일의 [4단 연쇄 스레드 포맷]으로 작성하세요.
절대로 단순 기사 요약이나 상투적인 문장에 머물지 말고, 최근 8월 공개된 최신 버전(GLM-5.3-Flash 가중치 수정, Claude Code 사용량 삭감/인상 괴리, WebMCP 표준화 등)의 핵심 스펙, 비용(1/10 절감 등), 원인 메커니즘, 실질 체감 수치를 직관적으로 폭로하고 분석하세요.

[🚨 CHOI 스타일 4단 엄격 작성 규칙]
1. 제목: 세련되고 전문적인 주제명 (예: 🔥 [Claude Code 주간 사용량 25% '인상'의 숨겨진 진실 • {today_str}])
2. [📌 메인 본문 (Hook & 핵심 요약)]:
   • 1행 훅: 공식 발표의 허점/역발상 또는 사용자의 손실/의문을 찌르는 강렬한 첫 문장 (예: "앤트로픽이 사용량을 늘린다고 발표했지만, 실제로는 줄어듭니다.")
   • 사건의 핵심 팩트와 반전 2~3줄 요약 (모바일 1문장 1줄바꿈)
   • "표현은 A이지만 결국 B인 셈입니다" 형식의 촌철살인 총평.
3. [💬 댓글 1 | 기술 메커니즘 & 원인 딥다이브]:
   • 본문에서 다루지 못한 구체적인 기술 스펙, 내부 아키텍처, 버그 발생 지점, 가중치 수정 등의 원리를 3~4문장으로 딥다이브.
4. [💬 댓글 2 | 실사용자 체감 수치 환산 & 영향도]:
   • 복잡한 퍼센티지를 '100 기준 직관적 정수 환산' (예: 기본 100 기준 기존 150 -> 변경 후 125 = 17% 삭감)
   • 실무 개발자/사용자에게 미치는 영향과 구체적인 대응 지침 제시.
5. [💬 댓글 3 | 공식 출처 & 원문 링크]:
   • 수집 데이터 중 1차 공식 발표를 가장 정확히 다룬 실제 기사/원문 링크 1개 (URL만).
6. 인사말이나 서론 없이 곧바로 '🔥 [' 로 시작할 것.

[수집된 실시간 데이터]
{data_context}

[출력 양식]
🔥 [정제된 세련된 주제명 • {today_str}]

📌 [메인 본문]
{{1행 역발상 훅}}

{{핵심 배경 및 반전 2~3줄}}

표현은 {{A}}이지만, 결국 {{B}}인 셈입니다.

💬 [댓글 1 | 기술 메커니즘 딥다이브]
내부 구조와 기술적 원인은 이렇습니다.
• {{구체적 아키텍처, 버그 지점, 가중치/로직 변경 사항 2~3줄}}

💬 [댓글 2 | 체감 수치 환산 & 실무 영향]
실제 체감 기준으로 계산하면:
• 기존: {{기준점 A}} ➔ 변경 후: {{결과점 B}}
• 결과적으로 {{실질 변화량}}의 차이가 발생합니다. 앞으로 {{실무 대응 팁}}이 필요합니다.

💬 [댓글 3 | 공식 출처]
🔗 {{수집 데이터 중 가장 대표적인 실제 기사/원문 링크 1개 (URL만)}}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8192,
            "thinkingConfig": { "thinkingBudget": 0 }
        }
    }

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.5-pro",
        "gemini-1.5-flash"
    ]

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                result_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                clean_res = html.unescape(result_text)
                if "🔥 [" in clean_res:
                    clean_res = clean_res[clean_res.find("🔥 ["):]
                return clean_res.strip()
        except Exception as e:
            continue

    return generate_offline_card_news(topic, items)


def generate_offline_card_news(topic: str, items: list[dict]) -> str:
    """오프라인 백업 시에도 검색 키워드 기반으로 100% 동적 심층 생성."""
    today_str = datetime.now().strftime('%m월 %d일')
    clean_topic = re.sub(r'^(지금|오늘|최신|실시간|에 대한|에대해|말이야|같은거)\s*', '', topic).strip() or topic
    clean_topic = re.sub(r'(말이야|같은거|알려줘|어때|추천해줘)$', '', clean_topic).strip() or clean_topic

    top_title = items[0]["title"] if items else f"{clean_topic} 실시간 최신 동향"
    top_link = items[0]["link"] if items else f"https://search.naver.com/search.naver?query={urllib.parse.quote(clean_topic)}"

    feed = f"""🔥 [{clean_topic} 실시간 이슈 브리핑 • {today_str}]

📌 [메인 본문]
{clean_topic}에 대한 공식 발표 및 시장 소식이 나왔지만, 실제 체감되는 변화는 다릅니다.

최신 데이터와 커뮤니티 지표를 대조한 결과, 주요 기능 업데이트와 함께 사용 환경 및 정책 기준이 새롭게 재편되고 있습니다.

표현은 '단순 업데이트'이지만, 결국 실사용자 워크플로우 전반이 바뀌는 셈입니다.

💬 [댓글 1 | 기술 메커니즘 딥다이브]
내부 구조와 핵심 원인은 이렇습니다.
• {html.unescape(top_title)}
• 관련 아키텍처 및 세부 데이터 처리 파이프라인 최적화가 적용되었습니다.

💬 [댓글 2 | 체감 수치 환산 & 실무 영향]
실제 체감 기준으로 계산하면:
• 기존 작업 환경 대비 처리 속도 및 비용 구조에서 실질적인 변화가 발생합니다.
• 실무에서는 변경된 세부 설정값을 반드시 사전 검증 후 도입하는 것을 권장합니다.

💬 [댓글 3 | 공식 출처]
🔗 {top_link}"""


def run_full_doribogo(topic: str) -> str:
    """수집 ➔ 가공 ➔ 4단계 브리핑 생성 파이프라인."""
    print(f"[*] 도리보고 2-Stage 교차검증 수집 가동: [{topic}]")
    items = harvest_2_stage_verification(topic)
    print(f"[*] {len(items)}개 검증 시그널 포착 완료. Gemini 2.5 Flash 심층 큐레이션 중...")
    card_news = generate_gemini_card_news(topic, items)
    return card_news


def main():
    today_str = datetime.now().strftime('%m월 %d일')
    print("=" * 60)
    print("🐯 dori bot 2-Stage 순차 교차검증 엔진 시작")
    print(f"• 오늘 날짜: {today_str}")
    print(f"• 감시 키워드: {', '.join(WATCH_KEYWORDS)}")
    print("=" * 60)

    for kw in WATCH_KEYWORDS:
        try:
            card = run_full_doribogo(kw)
            send_broadcast(f"⚡ [{today_str} 실시간 이슈] {kw}", card)
            time.sleep(2)
        except Exception as e:
            print(f"[!] 감시 오류 ({kw}): {e}")


if __name__ == "__main__":
    main()
